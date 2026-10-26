"""Schema checks for the field and observation tables (see docs/data_contract.md)."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

from cropews.config import SEASONS

FIELD_COLUMNS = ("field_id", "year", "crop_code", "EC_hcat_n", "field_size", "geometry")
OBSERVATION_COLUMNS = (
    "field_id",
    "year",
    "date",
    "coverage",
    "clear_fraction",
    "ndvi",
    "ndmi",
    "ndre",
    "evi",
    "msi",
)
NORMALISED_INDICES = ("ndvi", "ndmi", "ndre")
S1_OBSERVATION_COLUMNS = (
    "field_id",
    "year",
    "date",
    "orbit_state",
    "relative_orbit",
    "coverage",
    "vv_db",
    "vh_db",
    "vh_vv_db",
)
ORBIT_STATES = ("ascending", "descending")
# Plausible gamma0 range for agricultural fields; values outside indicate a unit or nodata bug.
BACKSCATTER_DB_RANGE = (-40.0, 10.0)


class DataContractError(ValueError):
    """Raised when a table violates the data contract."""


def _missing(df: pd.DataFrame, required: tuple[str, ...]) -> list[str]:
    return [c for c in required if c not in df.columns]


def field_errors(fields: gpd.GeoDataFrame) -> list[str]:
    missing = _missing(fields, FIELD_COLUMNS)
    if missing:
        return [f"missing columns: {missing}"]
    errors = []
    if fields.crs is None:
        errors.append("CRS is not set")
    if fields.duplicated(["field_id", "year"]).any():
        errors.append("duplicate (field_id, year)")
    if (fields["field_size"] <= 0).any():
        errors.append("field_size must be > 0")
    if not fields["year"].isin(SEASONS).all():
        errors.append(f"year outside {SEASONS[0]}-{SEASONS[-1]}")
    if (fields.geometry.is_empty | fields.geometry.isna()).any():
        errors.append("empty or missing geometry")
    elif not fields.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        errors.append("geometry must be Polygon or MultiPolygon")
    return errors


def observation_errors(obs: pd.DataFrame) -> list[str]:
    missing = _missing(obs, OBSERVATION_COLUMNS)
    if missing:
        return [f"missing columns: {missing}"]
    errors = []
    if obs.duplicated(["field_id", "date"]).any():
        errors.append("duplicate (field_id, date)")
    for col in ("coverage", "clear_fraction"):
        if not obs[col].between(0, 1).all():
            errors.append(f"{col} outside [0, 1]")
    for col in NORMALISED_INDICES:
        values = obs[col].dropna()
        if not values.between(-1, 1).all():
            errors.append(f"{col} outside [-1, 1]")
    return errors


def s1_observation_errors(obs: pd.DataFrame) -> list[str]:
    missing = _missing(obs, S1_OBSERVATION_COLUMNS)
    if missing:
        return [f"missing columns: {missing}"]
    errors = []
    if obs.duplicated(["field_id", "date", "orbit_state"]).any():
        errors.append("duplicate (field_id, date, orbit_state)")
    if not obs["orbit_state"].isin(ORBIT_STATES).all():
        errors.append(f"orbit_state not in {ORBIT_STATES}")
    if not obs["coverage"].between(0, 1).all():
        errors.append("coverage outside [0, 1]")
    for col in ("vv_db", "vh_db"):
        values = obs[col].dropna()
        if not values.between(*BACKSCATTER_DB_RANGE).all():
            errors.append(f"{col} outside {BACKSCATTER_DB_RANGE} dB")
    return errors


def validate_fields(fields: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    errors = field_errors(fields)
    if errors:
        raise DataContractError("; ".join(errors))
    return fields


def validate_observations(obs: pd.DataFrame) -> pd.DataFrame:
    errors = observation_errors(obs)
    if errors:
        raise DataContractError("; ".join(errors))
    return obs


def validate_s1_observations(obs: pd.DataFrame) -> pd.DataFrame:
    errors = s1_observation_errors(obs)
    if errors:
        raise DataContractError("; ".join(errors))
    return obs
