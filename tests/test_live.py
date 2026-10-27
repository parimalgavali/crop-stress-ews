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
            "CODE_TXT": ["Winterweichweizen", "Wintergerste", "Mähweiden"],
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
    lon = p["fields"]["features"][0]["geometry"]["coordinates"][0][0][0]
    assert 7 < lon < 9
