"""Winter emergence check (ADR 0016): a field's NDVI against its same-date district peers.

Uses the same peer residual as the stress label (ADR 0010), on clear Sentinel-2 dates from
1 November to 31 March before harvest. The scale is fitted on training seasons only.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from cropews.labels import (
    Z_THRESHOLD,
    clear_observations,
    fit_peer_scale,
    peer_residuals,
    score_peer,
)

WINTER_START_MONTH = 11
MIN_CLEAR_DATES = 2


def winter_observations(s2: pd.DataFrame) -> pd.DataFrame:
    """Clear Nov–Mar views; October is skipped because sowing dates differ by weeks."""
    obs = clear_observations(s2)
    month = obs["date"].dt.month
    return obs[(month >= WINTER_START_MONTH) | (month <= 3)].reset_index(drop=True)


def emergence_scores(
    s2: pd.DataFrame, train_years: Iterable[int], min_peers: int = 8
) -> pd.DataFrame:
    """One row per (field, season): median peer z of NDVI over the winter and the flag."""
    # Winter clear dates are sparse, so the scale is pooled over the whole winter per district
    # instead of per 10-day bin (otherwise many test dates have no fitted scale).
    res = peer_residuals(winter_observations(s2), min_peers).assign(doy_bin=0)
    scored = score_peer(res, fit_peer_scale(res, train_years))
    out = (
        scored.groupby(["field_id", "year", "district"])
        .agg(n_clear=("z_ndvi", "size"), z_ndvi=("z_ndvi", "median"))
        .reset_index()
    )
    out["weak_emergence"] = (out["z_ndvi"] < Z_THRESHOLD) & (out["n_clear"] >= MIN_CLEAR_DATES)
    return out


def spring_outcome(scores: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Attach y = 1 if the field had a spring stress event (ADR 0010 label) that season."""
    hit = events[["field_id", "year"]].drop_duplicates().assign(y=1)
    out = scores.merge(hit, on=["field_id", "year"], how="left")
    return out.assign(y=out["y"].fillna(0).astype(int))


def summarise(frame: pd.DataFrame) -> dict[str, float]:
    """Event rate with/without the flag and AUROC of the winter score for a spring event."""
    flagged = frame[frame["weak_emergence"]]
    rest = frame[~frame["weak_emergence"]]
    auroc = (
        float(roc_auc_score(frame["y"], -frame["z_ndvi"]))
        if frame["y"].nunique() == 2
        else float("nan")
    )
    return {
        "fields": float(len(frame)),
        "flagged": float(len(flagged)),
        "event_rate_flagged": float(flagged["y"].mean()) if len(flagged) else np.nan,
        "event_rate_other": float(rest["y"].mean()) if len(rest) else np.nan,
        "auroc": auroc,
    }


WET_DROP_DB = 3.0
WET_RAIN_MM = 20.0
WET_RAIN_DAYS = 7


def wet_dates(s1: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """Radar dates where VV fell >= 3 dB below the field's winter median for the same orbit
    direction after >= 20 mm of rain in the previous 7 days: a sign of standing water.
    """
    s1 = s1.assign(date=pd.to_datetime(s1["date"]).dt.normalize()).dropna(subset=["vv_db"])
    median = s1.groupby(["field_id", "year", "orbit_state"])["vv_db"].transform("median")
    s1 = s1.assign(vv_drop_db=median - s1["vv_db"])
    rain = (
        daily.assign(date=pd.to_datetime(daily["date"]).dt.normalize())
        .sort_values(["field_id", "date"])
        .reset_index(drop=True)
    )
    rain = rain.assign(
        rain_7d_mm=rain.groupby("field_id")["pr_mm"].transform(
            lambda x: x.rolling(WET_RAIN_DAYS, min_periods=WET_RAIN_DAYS).sum()
        )
    )[["field_id", "date", "rain_7d_mm"]]
    out = s1.merge(rain, on=["field_id", "date"], how="left")
    out["wet"] = (out["vv_drop_db"] >= WET_DROP_DB) & (out["rain_7d_mm"] >= WET_RAIN_MM)
    return out


def wet_summary(wet: pd.DataFrame) -> pd.DataFrame:
    """Per (field, season): radar dates, wet dates and the share of wet dates."""
    out = (
        wet.groupby(["field_id", "year"])
        .agg(n_radar=("wet", "size"), n_wet=("wet", "sum"))
        .reset_index()
    )
    return out.assign(wet_share=out["n_wet"] / out["n_radar"])
