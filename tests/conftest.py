import geopandas as gpd
import pytest
from shapely.geometry import box


@pytest.fixture
def raw_parcels() -> gpd.GeoDataFrame:
    """Europe-LAND-like parcels in EPSG:25832: two wheat fields, one small wheat, one maize."""
    return gpd.GeoDataFrame(
        {
            "field_id": ["a", "b", "c", "d"],
            "crop_code": [115, 115, 115, 411],
            "EC_hcat_n": ["winter_common_soft_wheat"] * 3 + ["green_silo_maize"],
            "field_size": [4.0, 3.0, 0.5, 6.0],
        },
        geometry=[
            box(0, 0, 200, 200),
            box(1000, 0, 1150, 200),
            box(0, 500, 70, 570),
            box(0, 0, 1, 1),
        ],
        crs="EPSG:25832",
    )
