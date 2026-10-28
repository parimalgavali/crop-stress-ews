import geopandas as gpd
from shapely.geometry import box

from cropews.data.fields import assign_districts, load_winter_wheat_fields, sample_fields


def test_load_keeps_only_winter_wheat_above_min_size(tmp_path, raw_parcels):
    path = tmp_path / "parcels.geoparquet"
    raw_parcels.to_parquet(path)

    fields = load_winter_wheat_fields(path, 2024, min_size_ha=1.0)

    assert sorted(fields["field_id"]) == ["a", "b"]
    assert (fields["year"] == 2024).all()
    assert fields["crop_code"].tolist() == ["115", "115"]
    assert fields.crs.to_epsg() == 25832


def test_assign_districts_uses_representative_point(raw_parcels):
    districts = gpd.GeoDataFrame(
        {"GEN": ["West", "East"]},
        geometry=[box(-10, -10, 500, 1000), box(500, -10, 2000, 1000)],
        crs="EPSG:25832",
    )
    out = assign_districts(raw_parcels, districts)
    assert out.set_index("field_id")["district"].to_dict() == {
        "a": "West",
        "b": "East",
        "c": "West",
        "d": "West",
    }


def test_assign_districts_outside_all_is_nan(raw_parcels):
    districts = gpd.GeoDataFrame(
        {"GEN": ["Far"]}, geometry=[box(1e6, 1e6, 2e6, 2e6)], crs="EPSG:25832"
    )
    assert assign_districts(raw_parcels, districts)["district"].isna().all()


def test_sample_fields_is_deterministic_and_capped(raw_parcels):
    assert (
        sample_fields(raw_parcels, 2, seed=1)["field_id"].tolist()
        == sample_fields(raw_parcels, 2, seed=1)["field_id"].tolist()
    )
    assert len(sample_fields(raw_parcels, 10)) == 4


def test_stable_sample_survives_edits_elsewhere_and_changes_by_season():
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point

    from cropews.data.fields import stable_sample

    ids = [f"LWK-{i}" for i in range(500)]
    parcels = gpd.GeoDataFrame({"field_id": ids}, geometry=[Point(i, 0) for i in range(500)])
    picked = set(stable_sample(parcels, 30, "2026/2027")["field_id"])
    dropped = sorted(picked)[0]
    edited = parcels[parcels["field_id"] != dropped].sample(frac=1, random_state=1)
    edited = gpd.GeoDataFrame(
        pd.concat([edited, gpd.GeoDataFrame({"field_id": ["LWK-new"]}, geometry=[Point(0, 1)])])
    )
    again = set(stable_sample(edited, 30, "2026/2027")["field_id"])
    assert len(picked - again) == 1 and dropped not in again
    assert len(again) == 30
    assert set(stable_sample(parcels, 30, "2027/2028")["field_id"]) != picked
