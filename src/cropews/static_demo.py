"""Compact per-season JSON for the static GitHub Pages demo (ADR 0014).

Same content the API serves (ADR 0012), pre-joined so the UI can run without a server:
dates, field polygons (EPSG:4326, rounded to ~1 m) and, per field and date, one
``[days, risk, level, [reason codes]]`` entry per horizon. Reason texts are stored once.
"""

from __future__ import annotations

import json
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from cropews.explain import TEXT

ATTRIBUTION = (
    "Fields: Europe-LAND harmonised IACS (CC BY 4.0, Land NRW). "
    "Imagery: Copernicus Sentinel-1/2 (modified). Weather: DWD (CC BY 4.0). "
    "Predictions: crop-stress-ews (portfolio demo, not agronomic advice)."
)
DECIMALS = 5


def _round(coords: Any) -> Any:
    if isinstance(coords, int | float):
        return round(float(coords), DECIMALS)
    return [_round(c) for c in coords]


def build_season(preds: pd.DataFrame, fields: gpd.GeoDataFrame, year: int) -> dict[str, Any]:
    """Demo payload for one season; fields without predictions are dropped."""
    p = preds[preds["year"] == year].sort_values(["field_id", "date", "horizon_days"])
    f = fields[(fields["year"] == year) & fields["field_id"].isin(p["field_id"])]
    f = f.sort_values("field_id")
    risk: dict[str, dict[str, list[list[Any]]]] = {}
    for row in p.itertuples(index=False):
        date = pd.Timestamp(row.date).date().isoformat()
        codes = [r["code"] for r in json.loads(row.reasons)]
        entry = [int(row.horizon_days), round(float(row.risk), 4), str(row.level), codes]
        risk.setdefault(str(row.field_id), {}).setdefault(date, []).append(entry)
    features = [
        {
            "type": "Feature",
            "id": r.field_id,
            "geometry": {"type": geom["type"], "coordinates": _round(geom["coordinates"])},
            "properties": {
                "field_id": r.field_id,
                "district": r.district,
                "area_ha": round(float(r.area_ha), 2),
            },
        }
        for r in f.itertuples(index=False)
        for geom in [mapping(r.geometry)]
    ]
    dates = sorted({pd.Timestamp(d).date().isoformat() for d in p["date"].unique()})
    return {
        "year": year,
        "attribution": ATTRIBUTION,
        "dates": dates,
        "reasons": {code: {"en": en, "de": de} for code, (en, de) in TEXT.items()},
        "fields": {"type": "FeatureCollection", "features": features},
        "risk": risk,
    }
