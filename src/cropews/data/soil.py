"""Field soil from the Geological Survey NRW soil map BK50, via WMS GetFeatureInfo (ADR 0030)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import geopandas as gpd
import pandas as pd
import requests

WMS = "https://www.wms.nrw.de/gd/bk050"
ATTRIBUTION = "Soil: Geologischer Dienst NRW, BK50, dl-de/by-2-0"
SOIL_FEATURES = ["nfk_mm", "gw_level", "sw_level"]


def _num(v: Any) -> float | None:
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def parse_feature(props: dict[str, Any]) -> dict[str, Any]:
    """BK50 attributes we use: soil type, texture, available water capacity in the root zone
    (nFK, mm), groundwater (GW_STUFE) and waterlogging (SW_STUFE) levels, 0 = none."""
    return {
        "soil_type": props.get("TYP_TEXT") or None,
        "texture": props.get("LUFA_TXT") or None,
        "nfk_mm": _num(props.get("NFK")),
        "gw_level": _num(props.get("GW_STUFE")),
        "sw_level": _num(props.get("SW_STUFE")),
    }


def soil_at(x: float, y: float, timeout: float = 30) -> dict[str, Any] | None:
    """BK50 polygon at an EPSG:25832 point; ``None`` outside the map (e.g. open-cast mines)."""
    params: dict[str, str | int] = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": "Bodentyp",
        "QUERY_LAYERS": "Bodentyp",
        "CRS": "EPSG:25832",
        "BBOX": f"{x - 5},{y - 5},{x + 5},{y + 5}",
        "WIDTH": 11,
        "HEIGHT": 11,
        "I": 5,
        "J": 5,
        "INFO_FORMAT": "application/geo+json",
        "FEATURE_COUNT": 1,
    }
    r = requests.get(WMS, params=params, timeout=timeout)
    r.raise_for_status()
    feats = r.json().get("features") or []
    return parse_feature(feats[0]["properties"]) if feats else None


def field_soils(fields: gpd.GeoDataFrame, workers: int = 8) -> pd.DataFrame:
    """One row per field_id, read at each field's representative point."""
    pts = fields.to_crs(25832).geometry.representative_point()

    def one(p: Any) -> dict[str, Any]:
        for _ in range(3):
            try:
                return soil_at(p.x, p.y) or {}
            except (requests.RequestException, ValueError):
                continue
        return {}

    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(one, pts))
    cols = ["soil_type", "texture", *SOIL_FEATURES]
    return pd.DataFrame(rows, columns=cols).assign(field_id=fields["field_id"].values)[
        ["field_id", *cols]
    ]
