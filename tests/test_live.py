from datetime import date

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from cropews.data.lwk import arable_parcels
from cropews.live import conditions, live_payload

AS_OF = date(2026, 11, 1)


def test_arable_parcels_filters_use_and_size():
    raw = pd.DataFrame(
        {
            "ID": [1, 2, 3],
            "AREA_HA": [3.0, 1.0, 5.0],
            "CODE_TXT": ["Winterweichweizen ", "Wintergerste", "Mähweiden"],
            "USE_TXT": ["Getreide", "Getreide", "Dauergrünland"],
            "VALIDFROM": [2026, 2026, 2026],
            "geometry": [box(0, 0, 1, 1)] * 3,
        }
    )
    out = arable_parcels(raw)
    assert out["field_id"].tolist() == ["LWK-1"]
    assert out.loc[0, "declared_crop"] == "Winterweichweizen"


def test_conditions_combines_sources():
    s2 = pd.DataFrame(
        {
            "field_id": ["a"] * 3,
            "date": [date(2026, 9, 20), date(2026, 10, 5), date(2026, 10, 28)],
            "clear_fraction": [1.0, 0.5, 0.9],
            "ndvi": [0.2, 0.9, 0.5],
            "ndmi": [0.0, 0.1, 0.2],
        }
    )
    s1 = pd.DataFrame(
        {
            "field_id": ["a"] * 3,
            "date": [date(2026, 10, 10), date(2026, 10, 22), date(2026, 10, 30)],
            "orbit_state": ["ascending", "ascending", "ascending"],
            "vv_db": [-12.0, -14.0, -10.0],
            "vh_vv_db": [-7.0, -7.0, -6.5],
        }
    )
    days = pd.date_range("2026-09-01", "2026-10-30").date
    daily = pd.DataFrame(
        {"field_id": "a", "date": days, "pr_mm": 1.0, "tas_c": 8.0, "tasmin_c": 2.0}
    )
    c = conditions(s2, s1, daily, AS_OF)["a"]
    assert c["s2_date"] == "2026-10-28" and c["s2_days_ago"] == 4
    assert c["ndvi_change"] == 0.3  # vs the 20 Sep clear view; the cloudy 5 Oct view is ignored
    assert c["vv_change_db"] == 3.0
    assert c["rain_30d_mm"] == 30.0 and c["tmin_7d_c"] == 2.0
    assert c["weather_to"] == "2026-10-30"


def test_missing_sources_and_payload():
    empty_s2 = pd.DataFrame(columns=["field_id", "date", "clear_fraction", "ndvi", "ndmi"])
    s1 = pd.DataFrame(
        {
            "field_id": ["a"],
            "date": [date(2026, 10, 30)],
            "orbit_state": ["descending"],
            "vv_db": [-11.0],
            "vh_vv_db": [-6.0],
        }
    )
    empty_w = pd.DataFrame(columns=["field_id", "date", "pr_mm", "tas_c", "tasmin_c"])
    cond = conditions(empty_s2, s1, empty_w, AS_OF)
    assert cond == {
        "a": {"s1_date": "2026-10-30", "s1_days_ago": 2, "vh_vv_db": -6.0, "vv_change_db": None}
    }
    fields = gpd.GeoDataFrame(
        {"field_id": ["a"], "district": ["Soest"], "area_ha": [3.0], "declared_crop": ["Mais"]},
        geometry=[box(440000, 5720000, 440100, 5720100)],
        crs="EPSG:25832",
    )
    p = live_payload(fields, cond, AS_OF, "attr")
    assert p["as_of"] == "2026-11-01"
    assert p["fields"]["features"][0]["properties"]["declared_crop"] == "Mais"
    assert p["fields"]["features"][0]["properties"]["wheat_p"] is None
    with_map = live_payload(fields, cond, AS_OF, "attr", wheat_p={"a": 0.81234})
    assert with_map["fields"]["features"][0]["properties"]["wheat_p"] == 0.812
    assert with_map["spring_monitoring"] == ["a"]
    assert p["spring_monitoring"] == []
    lon = p["fields"]["features"][0]["geometry"]["coordinates"][0][0][0]
    assert 7 < lon < 9


def test_health_problem_flags_missing_or_mostly_empty_payloads():
    from cropews.live import health_problem, run_health

    feats = {"features": [{}] * 4}
    assert health_problem(None) == "no live/latest.json was written"
    assert health_problem({"fields": {"features": []}, "conditions": {}}) == (
        "no parcels were sampled"
    )
    assert health_problem({"fields": feats, "conditions": {"a": {}}}) == (
        "only 1 of 4 parcels have data"
    )
    assert health_problem({"fields": feats, "conditions": dict.fromkeys("ab", {})}) is None
    h = run_health(4, 2, ["b", "a", "a"], [], 125)
    assert h == {
        "parcels": 4,
        "with_data": 2,
        "s1_scenes_skipped": ["a", "b"],
        "s2_scenes_skipped": [],
        "minutes": 2.1,
    }


def test_cache_since_only_trusts_a_cache_that_covers_the_fields_and_window():
    from datetime import date

    from cropews.live import cache_since

    meta = {"start": "2026-10-01", "through": "2026-11-20", "fields": ["a", "b"]}
    start, as_of = date(2026, 10, 1), date(2026, 11, 25)
    assert cache_since(meta, {"a"}, start, as_of) == date(2026, 11, 10)
    assert cache_since(meta, {"a", "c"}, start, as_of) == start
    assert cache_since(meta, {"a"}, date(2026, 9, 1), as_of) == date(2026, 9, 1)
    assert cache_since(meta, {"a"}, start, date(2026, 11, 1)) == start
    assert cache_since(None, {"a"}, start, as_of) == start


def test_merge_cached_keeps_old_rows_and_lets_new_rows_win():
    from datetime import date

    from cropews.live import merge_cached

    old = pd.DataFrame(
        {
            "field_id": ["a", "a", "z"],
            "date": pd.to_datetime(["2026-09-01", "2026-11-12", "2026-11-12"]),
            "ndvi": [0.1, 0.2, 0.9],
        }
    )
    new = pd.DataFrame({"field_id": ["a"], "date": pd.to_datetime(["2026-11-12"]), "ndvi": [0.3]})
    new.attrs["skipped_scenes"] = ["x"]
    out = merge_cached(old, new, {"a"}, date(2026, 10, 1), date(2026, 11, 25), ["field_id", "date"])
    assert out["ndvi"].tolist() == [0.3]
    assert out.attrs["skipped_scenes"] == ["x"]
    old2 = old.assign(date=pd.to_datetime(["2026-10-05", "2026-11-01", "2026-11-12"]))
    out2 = merge_cached(
        old2, new, {"a"}, date(2026, 10, 1), date(2026, 11, 25), ["field_id", "date"]
    )
    assert out2["ndvi"].tolist() == [0.1, 0.2, 0.3]
