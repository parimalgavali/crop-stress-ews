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


# Parcels at or above this crop-map probability enter spring monitoring (ADR 0018).
WHEAT_THRESHOLD = 0.5


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


FORECAST_DAYS = 5
FROST_C = 0.0


def forecast_summary(daily_fc: pd.DataFrame, as_of: date) -> dict[str, Any]:
    """Rain and lowest temperature over the next ``FORECAST_DAYS`` days after ``as_of`` (ICON)."""
    d = daily_fc.assign(date=pd.to_datetime(daily_fc["date"]).dt.date)
    d = d[(d["date"] > as_of) & (d["date"] <= as_of + timedelta(FORECAST_DAYS))]
    if len(d) < FORECAST_DAYS:
        return {}
    return {
        "fc_to": d["date"].max(),
        "fc_rain_5d_mm": round(float(d["pr_mm"].sum()), 1),
        "fc_tmin_5d_c": round(float(d["tasmin_c"].min()), 1),
        "fc_frost_days": int((d["tasmin_c"] < FROST_C).sum()),
    }


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
    wheat_p: dict[str, float] | None = None,
    forecast: dict[str, dict[str, Any]] | None = None,
    risk: dict[str, dict[str, Any]] | None = None,
    forecasts: list[dict[str, Any]] | None = None,
    winter: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """``wheat_p``: field_id -> P(winter wheat) (ADR 0018); ``forecast``: district -> summary
    from :func:`forecast_summary` (ADR 0019)."""
    wheat_p = wheat_p or {}
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
                "wheat_p": _clean(wheat_p.get(r.field_id)),
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
        "forecast": {k: {n: _clean(v) for n, v in d.items()} for k, d in (forecast or {}).items()},
        "risk": risk or {},
        "forecasts": forecasts or [],
        "winter": winter or {},
        "spring_monitoring": sorted(k for k, p in wheat_p.items() if p >= WHEAT_THRESHOLD),
    }


# A live run is unhealthy if fewer than this share of sampled parcels got any data (ADR 0023).
MIN_DATA_SHARE = 0.5


def run_health(
    parcels: int, with_data: int, skipped_s1: list[str], skipped_s2: list[str], seconds: float
) -> dict[str, Any]:
    """Per-run health block for ``latest.json``; checked by scripts/check_live_health.py."""
    return {
        "parcels": parcels,
        "with_data": with_data,
        "s1_scenes_skipped": sorted(set(skipped_s1)),
        "s2_scenes_skipped": sorted(set(skipped_s2)),
        "minutes": round(seconds / 60, 1),
    }


def health_problem(payload: dict[str, Any] | None) -> str | None:
    """Why a live payload is unhealthy, or None if it is fine."""
    if not payload:
        return "no live/latest.json was written"
    parcels = len(payload.get("fields", {}).get("features", []))
    with_data = len(payload.get("conditions", {}))
    if parcels == 0:
        return "no parcels were sampled"
    if with_data < MIN_DATA_SHARE * parcels:
        return f"only {with_data} of {parcels} parcels have data"
    return None


# Incremental extraction (ADR 0025): re-read this many days before the cache's last run, so late
# scenes and scenes skipped after read errors get another chance.
CACHE_OVERLAP_DAYS = 10


def cache_since(meta: dict[str, Any] | None, ids: set[str], start: date, as_of: date) -> date:
    """First image date to extract for a district: ``start`` unless the cache covers its fields."""
    if not meta or not ids <= set(meta.get("fields", [])):
        return start
    through = date.fromisoformat(meta["through"])
    if date.fromisoformat(meta["start"]) > start or through > as_of:
        return start
    return max(start, through - timedelta(CACHE_OVERLAP_DAYS))


def merge_cached(
    cached: pd.DataFrame | None,
    new: pd.DataFrame,
    ids: set[str],
    start: date,
    as_of: date,
    keys: list[str],
) -> pd.DataFrame:
    """Cached rows of these fields within [start, as_of] plus new rows; new rows win on ``keys``."""
    if cached is None or cached.empty:
        return new
    dates = pd.to_datetime(cached["date"])
    old = cached[cached["field_id"].isin(ids) & (dates >= pd.Timestamp(start))]
    old = old[pd.to_datetime(old["date"]) <= pd.Timestamp(as_of) + pd.Timedelta(days=1)]
    out = pd.concat([old, new], ignore_index=True).drop_duplicates(keys, keep="last")
    out = out.sort_values(keys).reset_index(drop=True)
    out.attrs = new.attrs
    return out
