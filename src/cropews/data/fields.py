"""Load NRW winter-wheat parcels from the Europe-LAND harmonised IACS inventory."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from cropews.config import WINTER_WHEAT_HCAT, WORKING_CRS
from cropews.data.contract import validate_fields

_COLUMNS = ["field_id", "crop_code", "EC_hcat_n", "field_size", "geometry"]


def load_winter_wheat_fields(
    path: str | Path, year: int, min_size_ha: float = 0.0
) -> gpd.GeoDataFrame:
    fields = gpd.read_parquet(path, columns=_COLUMNS)
    fields = fields[
        (fields["EC_hcat_n"] == WINTER_WHEAT_HCAT) & (fields["field_size"] >= min_size_ha)
    ]
    fields = fields.to_crs(WORKING_CRS).assign(
        year=year, crop_code=lambda d: d["crop_code"].astype(str)
    )
    return validate_fields(fields.reset_index(drop=True))


def assign_districts(
    fields: gpd.GeoDataFrame, districts: gpd.GeoDataFrame, name_col: str = "GEN"
) -> gpd.GeoDataFrame:
    """Attach the district containing each field's representative point (NaN if none)."""
    points = gpd.GeoDataFrame(
        {"_row": range(len(fields))},
        geometry=fields.geometry.representative_point().values,
        crs=fields.crs,
    )
    joined = gpd.sjoin(
        points, districts[[name_col, "geometry"]].to_crs(fields.crs), predicate="within"
    )
    district = joined.drop_duplicates("_row").set_index("_row")[name_col]
    out = fields.copy()
    out["district"] = pd.Series(range(len(fields))).map(district).values
    return out


def sample_fields(fields: gpd.GeoDataFrame, n: int, seed: int = 0) -> gpd.GeoDataFrame:
    return fields.sample(min(n, len(fields)), random_state=seed).reset_index(drop=True)
