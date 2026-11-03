"""Model features from the 5-day grid. Every feature at row t uses only rows at or before t."""

from __future__ import annotations

import numpy as np
import pandas as pd

S2_FEATURES = ("ndvi", "ndmi", "ndre")
S1_FEATURES = ("vh_db_asc", "vh_vv_db_asc", "vh_db_desc", "vh_vv_db_desc")
DAYS_SINCE = ("s2_days_since", "s1_asc_days_since", "s1_desc_days_since")
WINDOW_STEPS = 6  # 30 days
SHORT_STEPS = 3  # 15 days
GDD_BASE_C = 0.0
HEAT_C = 30.0


def _rolling(g: pd.DataFrame, values: pd.Series, n: int, how: str) -> pd.Series:
    return values.groupby(g["field_id"]).transform(lambda s: s.rolling(n, min_periods=1).agg(how))


def _slope(g: pd.DataFrame, col: str) -> pd.Series:
    """Change per day between the two latest observations, carried forward."""
    obs = g.loc[g[col].notna(), ["field_id", "date", col]]
    prev = obs.groupby("field_id")[[col, "date"]].shift()
    slope = pd.Series(np.nan, index=g.index)
    slope.loc[obs.index] = (obs[col] - prev[col]) / (obs["date"] - prev["date"]).dt.days
    return slope.groupby(g["field_id"]).ffill()


def build_features(
    grid: pd.DataFrame, peer_key: str | None = None, min_peers: int = 1
) -> pd.DataFrame:
    """One feature row per grid row; needs a ``district`` column for peer anomalies.

    ``peer_key`` (a column in ``grid``, e.g. a soil water class) narrows the peer group to
    (peer_key, date); groups smaller than ``min_peers`` fall back to the district median.
    """
    g = grid.sort_values(["field_id", "date"]).reset_index(drop=True)
    keep = ["field_id", "year", "date", "district"] + ([peer_key] if peer_key else [])
    out = g[keep].copy()
    out["doy"] = g["date"].dt.dayofyear
    for col in (*S2_FEATURES, *S1_FEATURES):
        last = g[col].groupby(g["field_id"]).ffill()
        out[f"{col}_last"] = last
        out[f"{col}_slope"] = _slope(g, col)
        out[f"{col}_mean15d"] = _rolling(g, g[col], SHORT_STEPS, "mean")
    for col in S2_FEATURES:
        if peer_key:
            peer = out.groupby([peer_key, "date"])[f"{col}_last"].transform("median")
            if min_peers > 1:
                support = out.groupby([peer_key, "date"])[f"{col}_last"].transform("size")
                fallback = out.groupby(["district", "date"])[f"{col}_last"].transform("median")
                peer = peer.where(support >= min_peers, fallback)
        else:
            peer = out.groupby(["district", "date"])[f"{col}_last"].transform("median")
        out[f"{col}_peer_anom"] = out[f"{col}_last"] - peer
    for col in DAYS_SINCE:
        out[col] = g[col]
    out["water_balance_30d"] = _rolling(g, g["pr_mm"] - g["et0_mm"], WINDOW_STEPS, "sum")
    out["hot_steps_30d"] = _rolling(g, (g["tasmax_c"] >= HEAT_C).astype(float), WINDOW_STEPS, "sum")
    out["vpd_15d"] = _rolling(g, g["vpd_kpa"], SHORT_STEPS, "mean")
    out["soil_moist_pct"] = g["soil_moist_pct"]
    daily_gdd = (g["tas_c"] - GDD_BASE_C).clip(lower=0) * g["weather_days"]
    out["gdd"] = daily_gdd.groupby(g["field_id"]).cumsum()
    return out


def feature_columns(features: pd.DataFrame) -> list[str]:
    return [c for c in features.columns if c not in ("field_id", "year", "date", "district")]
