"""Current field conditions for the live season (ADR 0015); no model scores, only observations."""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from cropews.static_demo import _round

CLEAR_THRESHOLD = 0.8
RAIN_DAYS = 30
TEMP_DAYS = 7
CHANGE_MIN_GAP_DAYS = 20


def _clean(v: Any) -> Any:
    if isinstance(v, float):
        return None if math.isnan(v) else round(v, 3)
    if isinstance(v, date):
        return v.isoformat()
    return v


def optical(s2: pd.DataFrame, as_of: date) -> dict[str, dict[str, Any]]:
    """Latest clear Sentinel-2 view and the NDVI change since a clear view ≥ 20 days earlier."""
    clear = s2[
        (s2["clear_fraction"] >= CLEAR_THRESHOLD) & (pd.to_datetime(s2["date"]).dt.date <= as_of)
    ]
    out: dict[str, dict[str, Any]] = {}
    for fid, g in clear.assign(date=pd.to_datetime(clear["date"]).dt.date).groupby("field_id"):
        g = g.sort_values("date")
        last = g.iloc[-1]
        earlier = g[g["date"] <= last["date"] - timedelta(CHANGE_MIN_GAP_DAYS)]
        change = float(last["ndvi"] - earlier.iloc[-1]["ndvi"]) if len(earlier) else float("nan")
        out[str(fid)] = {
            "s2_date": last["date"],
            "s2_days_ago": (as_of - last["date"]).days,
            "ndvi": float(last["ndvi"]),
            "ndmi": float(last["ndmi"]),
            "ndvi_change": change,
        }
    return out


def radar(s1: pd.DataFrame, as_of: date) -> dict[str, dict[str, Any]]:
    """Latest Sentinel-1 view; VV change vs the median of earlier views in the same orbit."""
    s1 = s1.assign(date=pd.to_datetime(s1["date"]).dt.date)
    s1 = s1[s1["date"] <= as_of]
    out: dict[str, dict[str, Any]] = {}
    for fid, g in s1.groupby("field_id"):
        g = g.sort_values("date")
        last = g.iloc[-1]
        same = g[(g["orbit_state"] == last["orbit_state"]) & (g["date"] < last["date"])]
        change = float(last["vv_db"] - same["vv_db"].median()) if len(same) else float("nan")
        out[str(fid)] = {
            "s1_date": last["date"],
            "s1_days_ago": (as_of - last["date"]).days,
            "vh_vv_db": float(last["vh_vv_db"]),
            "vv_change_db": change,
        }
    return out


def weather(daily: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """30-day rain and 7-day mean/min temperature up to the last available weather day."""
    daily = daily.assign(date=pd.to_datetime(daily["date"]).dt.date)
    out: dict[str, dict[str, Any]] = {}
    for fid, g in daily.dropna(subset=["pr_mm"]).groupby("field_id"):
        end = g["date"].max()
        rain = g[g["date"] > end - timedelta(RAIN_DAYS)]
        temp = g[g["date"] > end - timedelta(TEMP_DAYS)]
        out[str(fid)] = {
            "weather_to": end,
            "rain_30d_mm": float(rain["pr_mm"].sum()),
            "tmean_7d_c": float(temp["tas_c"].mean()),
            "tmin_7d_c": float(temp["tasmin_c"].min()),
        }
    return out


def conditions(
    s2: pd.DataFrame, s1: pd.DataFrame, daily: pd.DataFrame, as_of: date
) -> dict[str, dict[str, Any]]:
    parts = [optical(s2, as_of), radar(s1, as_of), weather(daily)]
    ids = sorted(set().union(*parts))
    return {fid: {k: _clean(v) for p in parts for k, v in p.get(fid, {}).items()} for fid in ids}


def live_payload(
    fields: gpd.GeoDataFrame,
    cond: dict[str, dict[str, Any]],
    as_of: date,
    attribution: str,
) -> dict[str, Any]:
    f = fields.to_crs(4326).sort_values("field_id")
    features = [
        {
            "type": "Feature",
            "id": r.field_id,
            "geometry": {"type": g["type"], "coordinates": _round(g["coordinates"])},
            "properties": {
                "field_id": r.field_id,
                "district": r.district,
                "area_ha": round(float(r.area_ha), 2),
                "declared_crop": r.declared_crop,
                "level": None,
            },
        }
        for r in f.itertuples(index=False)
        for g in [mapping(r.geometry)]
    ]
    return {
        "as_of": as_of.isoformat(),
        "attribution": attribution,
        "fields": {"type": "FeatureCollection", "features": features},
        "conditions": {k: v for k, v in cond.items() if k in set(f["field_id"])},
    }
