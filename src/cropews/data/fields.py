"""Load NRW winter-wheat parcels from the Europe-LAND harmonised IACS inventory."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
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


def load_parcels(
    path: str | Path, year: int, crop_codes: Iterable[str], min_size_ha: float = 0.0
) -> gpd.GeoDataFrame:
    """Parcels of any of ``crop_codes`` (NRW crop codes, as in Europe-LAND ``crop_code``)."""
    fields = gpd.read_parquet(path, columns=_COLUMNS)
    fields = fields.assign(crop_code=fields["crop_code"].astype(str))
    fields = fields[
        fields["crop_code"].isin(set(crop_codes)) & (fields["field_size"] >= min_size_ha)
    ]
    return validate_fields(fields.to_crs(WORKING_CRS).assign(year=year).reset_index(drop=True))


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


def stable_sample(fields: gpd.GeoDataFrame, n: int, salt: str) -> gpd.GeoDataFrame:
    """The n parcels with the smallest hash of (salt, field_id).

    Unlike ``sample_fields``, edits elsewhere in the parcel file don't reshuffle the sample:
    only parcels that disappear drop out (ADR 0015). Salt with the season for a new yearly draw.
    """
    key = fields["field_id"].map(lambda f: hashlib.sha256(f"{salt}:{f}".encode()).hexdigest())
    return fields.loc[key.sort_values(kind="stable").index[:n]].reset_index(drop=True)
