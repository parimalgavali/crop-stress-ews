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
