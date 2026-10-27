"""Sequence tensors from the 5-day grid for the US-09 models (ADR 0011).

Each prediction row (field, season, t) sees a window of the last ``w`` grid steps ending at t,
so a model can never use rows after t. Missing values stay NaN here; the observed mask and the
days since each channel was last observed are derived per window (GRU-D inputs).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from cropews.config import HORIZONS_DAYS
from cropews.labels import MIN_PEERS

STEP_DAYS = 5
DELTA_SCALE_DAYS = 30.0
PEER_INDICES = ("ndvi", "ndmi", "ndre")
CHANNEL_GROUPS: dict[str, tuple[str, ...]] = {
    "s2": ("ndvi", "ndmi", "ndre", "evi", "msi", *(f"{c}_peer" for c in PEER_INDICES)),
    "s1": (
        "vv_db_asc",
        "vh_db_asc",
        "vh_vv_db_asc",
        "vv_db_desc",
        "vh_db_desc",
        "vh_vv_db_desc",
    ),
    "weather": (
        "pr_mm",
        "tas_c",
        "tasmin_c",
        "tasmax_c",
        "hurs_pct",
        "vpd_kpa",
        "et0_mm",
        "soil_moist_pct",
    ),
}
TARGETS = tuple(f"onset_{h}d" for h in HORIZONS_DAYS)


def channels(groups: Iterable[str]) -> list[str]:
    return ["doy", *(c for g in groups for c in CHANNEL_GROUPS[g])]


def add_peer_channels(grid: pd.DataFrame, min_peers: int = MIN_PEERS) -> pd.DataFrame:
    """Departure from the same-date district median of clear fields (the label's reference)."""
    out = grid.copy()
    by = out.groupby(["district", "date"])
    for c in PEER_INDICES:
        n = by[c].transform("count")
        out[f"{c}_peer"] = (out[c] - by[c].transform("median")).where(n >= min_peers)
    out["doy"] = out["date"].dt.dayofyear.astype(float)
    return out


@dataclass
class SequenceSet:
    """``x``: (N, T, C) with NaN for missing; ``y``: (N, T, H) with NaN for undefined targets."""

    x: np.ndarray
    y: np.ndarray
    keys: pd.DataFrame  # one row per field-season: field_id, year, district
    dates: np.ndarray  # (N, T) datetime64
    channels: list[str]


def to_sequences(frame: pd.DataFrame, cols: list[str]) -> SequenceSet:
    """Reshape a merged grid + label frame into per field-season sequences of equal length."""
    f = frame.sort_values(["year", "field_id", "date"]).reset_index(drop=True)
    sizes = f.groupby(["year", "field_id"]).size()
    if sizes.nunique() != 1:
        raise ValueError("every field-season needs the same number of grid steps")
    n, t = len(sizes), int(sizes.iloc[0])
    keys = f.groupby(["year", "field_id"], sort=True).first().reset_index()
    return SequenceSet(
        x=f[cols].to_numpy(np.float32).reshape(n, t, len(cols)),
        y=f[list(TARGETS)].to_numpy(np.float32).reshape(n, t, len(TARGETS)),
        keys=keys[["field_id", "year", "district"]],
        dates=f["date"].to_numpy().reshape(n, t),
        channels=list(cols),
    )


def fit_scaler(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-channel mean/SD over observed values; fit on training seasons only."""
    flat = x.reshape(-1, x.shape[-1])
    mean, sd = np.nanmean(flat, axis=0), np.nanstd(flat, axis=0)
    return mean.astype(np.float32), np.where(sd > 0, sd, 1.0).astype(np.float32)


def windows(x: np.ndarray, w: int) -> np.ndarray:
    """(N, T, C) -> (N * T, w, C): row (n, t) holds steps t-w+1..t, left-padded with NaN."""
    n, t, c = x.shape
    padded = np.concatenate([np.full((n, w - 1, c), np.nan, x.dtype), x], axis=1)
    idx = np.arange(t)[:, None] + np.arange(w)[None, :]
    return padded[:, idx].reshape(n * t, w, c)


def mask_and_delta(xw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Observed mask and GRU-D time gaps: days since the previous observation, scaled."""
    m = ~np.isnan(xw)
    d = np.zeros(xw.shape, np.float32)
    for s in range(1, xw.shape[1]):
        d[:, s] = np.where(m[:, s - 1], STEP_DAYS, d[:, s - 1] + STEP_DAYS)
    return m.astype(np.float32), d / DELTA_SCALE_DAYS


def model_inputs(
    seq: SequenceSet, mean: np.ndarray, sd: np.ndarray, w: int
) -> dict[str, np.ndarray]:
    """Standardised windows (missing -> 0, the training mean), mask, delta and targets."""
    xw = windows((seq.x - mean) / sd, w)
    m, d = mask_and_delta(xw)
    return {
        "x": np.nan_to_num(xw, nan=0.0).astype(np.float32),
        "m": m,
        "d": d,
        "y": seq.y.reshape(-1, seq.y.shape[-1]),
    }


def row_index(seq: SequenceSet) -> pd.DataFrame:
    """Field, year and date for each window row, in :func:`windows` order."""
    n, t = seq.dates.shape
    return pd.DataFrame(
        {
            "field_id": np.repeat(seq.keys["field_id"].to_numpy(), t),
            "year": np.repeat(seq.keys["year"].to_numpy(), t),
            "date": seq.dates.reshape(-1),
        }
    )
