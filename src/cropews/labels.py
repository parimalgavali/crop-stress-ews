"""Stress-onset labels from Sentinel-2 anomalies against a training-only baseline (ADR 0007).

A field is *below* on a clear date if NDVI or NDMI is more than 1.5 SD under the mean of the same
district and 10-day day-of-year bin, fitted on training seasons only. An event starts on the first
of at least two consecutive below dates (onset before the senescence cutoff) and ends on the next
clear date that is not below (recovery).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd

from cropews.config import HORIZONS_DAYS

LABEL_INDICES = ("ndvi", "ndmi")
CLEAR_THRESHOLD = 0.8
Z_THRESHOLD = -1.5
MIN_CONSECUTIVE = 2
DOY_BIN_DAYS = 10
MIN_BASELINE_N = 20
SENESCENCE_CUTOFF = "06-30"


def clear_observations(s2: pd.DataFrame) -> pd.DataFrame:
    obs = s2[s2["clear_fraction"] >= CLEAR_THRESHOLD].dropna(subset=list(LABEL_INDICES))
    obs = obs.assign(date=pd.to_datetime(obs["date"]))
    return obs.assign(doy_bin=(obs["date"].dt.dayofyear - 1) // DOY_BIN_DAYS)


def fit_baseline(obs: pd.DataFrame, train_years: Iterable[int]) -> pd.DataFrame:
    """Mean/SD per (district, doy_bin) from training seasons only."""
    train = obs[obs["year"].isin(tuple(train_years))]
    if train.empty:
        raise ValueError("no training-season observations to fit the baseline")
    agg = {f"{i}_{s}": (i, s) for i in LABEL_INDICES for s in ("mean", "std")}
    base = train.groupby(["district", "doy_bin"]).agg(**agg, n=("ndvi", "size")).reset_index()
    return base[base["n"] >= MIN_BASELINE_N].reset_index(drop=True)


def score(obs: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    """Add z-scores and the `below` flag; drops dates without a baseline."""
    out = obs.merge(baseline, on=["district", "doy_bin"], how="inner")
    below = np.zeros(len(out), dtype=bool)
    for i in LABEL_INDICES:
        out[f"z_{i}"] = (out[i] - out[f"{i}_mean"]) / out[f"{i}_std"]
        below |= (out[f"z_{i}"] < Z_THRESHOLD).to_numpy()
    out["below"] = below
    keep = ["field_id", "year", "district", "date", *(f"z_{i}" for i in LABEL_INDICES), "below"]
    return out[keep].sort_values(["field_id", "date"]).reset_index(drop=True)


def find_events(scored: pd.DataFrame) -> pd.DataFrame:
    """One row per event: field, onset (first below date) and recovery (NaT if none)."""
    events = []
    for (field_id, year), g in scored.groupby(["field_id", "year"], sort=False):
        cutoff = pd.Timestamp(f"{year}-{SENESCENCE_CUTOFF}")
        dates, below = g["date"].to_list(), g["below"].to_numpy()
        i = 0
        while i < len(below):
            if not below[i]:
                i += 1
                continue
            j = i
            while j < len(below) and below[j]:
                j += 1
            if j - i >= MIN_CONSECUTIVE and dates[i] <= cutoff:
                recovery = dates[j] if j < len(dates) else pd.NaT
                events.append(
                    {"field_id": field_id, "year": year, "onset": dates[i], "recovery": recovery}
                )
            i = j
    return pd.DataFrame(events, columns=["field_id", "year", "onset", "recovery"])


def make_targets(
    keys: pd.DataFrame,
    events: pd.DataFrame,
    scored: pd.DataFrame,
    horizons: Sequence[int] = HORIZONS_DAYS,
) -> pd.DataFrame:
    """Targets per (field, grid date t): ``onset_{h}d`` = an event starts in (t, t + h].

    Targets are NaN when the field is in an event at t (onset <= t < recovery), when there is no
    clear observation in (t, t + h] to confirm or rule out an onset, or when t + h is after the
    senescence cutoff.
    """
    out = keys[["field_id", "year", "date"]].copy()
    out["date"] = pd.to_datetime(out["date"])
    t = out["date"].to_numpy()
    in_event = np.zeros(len(out), dtype=bool)
    first_onset_after = np.full(len(out), np.datetime64("NaT"), dtype="datetime64[ns]")
    by_field = {k: g for k, g in events.groupby("field_id")}
    obs_by_field = {k: np.sort(g["date"].to_numpy()) for k, g in scored.groupby("field_id")}
    next_obs = np.full(len(out), np.datetime64("NaT"), dtype="datetime64[ns]")

    for idx, (field_id, date) in enumerate(zip(out["field_id"], t, strict=True)):
        ev = by_field.get(field_id)
        if ev is not None:
            recovery = ev["recovery"].fillna(pd.Timestamp.max).to_numpy()
            onset = ev["onset"].to_numpy()
            in_event[idx] = bool(((onset <= date) & (date < recovery)).any())
            later = onset[onset > date]
            if len(later):
                first_onset_after[idx] = later.min()
        dates = obs_by_field.get(field_id)
        if dates is not None:
            k = np.searchsorted(dates, date, side="right")
            if k < len(dates):
                next_obs[idx] = dates[k]

    out["in_event"] = in_event
    cutoff = pd.to_datetime(out["year"].astype(str) + "-" + SENESCENCE_CUTOFF).to_numpy()
    for h in horizons:
        end = t + np.timedelta64(h, "D")
        hit = first_onset_after <= end
        observable = next_obs <= end
        target = np.where(hit, 1.0, 0.0)
        target[in_event | ~observable | (end > cutoff)] = np.nan
        out[f"onset_{h}d"] = target
    return out
