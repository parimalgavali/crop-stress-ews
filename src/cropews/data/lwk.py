"""Current-year declared parcels from the NRW Chamber of Agriculture (LWK), ADR 0015."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from cropews.config import WORKING_CRS

LWK_TSCHLAG_URL = (
    "https://www.opengeodata.nrw.de/produkte/umwelt_klima/bodennutzung/landwirtschaft/"
    "LWK-TSCHLAG_EPSG25832_Shape.zip"
)
LWK_ATTRIBUTION = "Landwirtschaftskammer NRW, dl-de/by-2-0"
# USE_TXT groups that are arable land (excludes grassland, permanent crops, set-aside, other).
ARABLE_USES = frozenset(
    {
        "Getreide",
        "Ackerfutter",
        "Hackfrüchte",
        "Ölsaaten",
        "Gemüse",
        "Eiweißpflanzen",
        "Energiepflanzen",
    }
)


def arable_parcels(raw: pd.DataFrame, min_size_ha: float = 2.0) -> pd.DataFrame:
    """Arable parcels of at least ``min_size_ha``, with the current declared crop kept."""
    keep = raw["USE_TXT"].isin(ARABLE_USES) & (raw["AREA_HA"] >= min_size_ha)
    out = raw[keep]
    return out.assign(
        field_id="LWK-" + out["ID"].astype(str),
        year=out["VALIDFROM"].astype(int),
        area_ha=out["AREA_HA"].astype(float),
        declared_crop=out["CODE_TXT"].astype(str),
    )[["field_id", "year", "area_ha", "declared_crop", "geometry"]].reset_index(drop=True)


def load_arable_parcels(path: str | Path, min_size_ha: float = 2.0) -> gpd.GeoDataFrame:
    cols = ["ID", "AREA_HA", "CODE_TXT", "USE_TXT", "VALIDFROM"]
    raw = gpd.read_file(path, columns=cols, engine="pyogrio")
    return gpd.GeoDataFrame(arable_parcels(raw, min_size_ha), crs=raw.crs).to_crs(WORKING_CRS)
