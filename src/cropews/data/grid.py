"""Regular 5-day grid joining Sentinel-2, Sentinel-1 and weather with explicit observed masks.

Each grid row (field, t) summarises the step (t - step, t]. Satellite values are taken only from
observations inside the step and are never forward-filled; ``*_observed`` flags and
``*_days_since`` (days since the latest observation on or before t) carry the missingness.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from cropews.config import PREDICTION_WINDOW

STEP_DAYS = 5
S2_CLEAR_THRESHOLD = 0.8
S2_VALUES = ("ndvi", "ndmi", "ndre", "evi", "msi")
S1_VALUES = ("vv_db", "vh_db", "vh_vv_db")
ORBIT_SUFFIX = {"ascending": "asc", "descending": "desc"}
WEATHER_AGG = {
    "pr_mm": "sum",
    "tas_c": "mean",
    "tasmin_c": "min",
    "tasmax_c": "max",
    "hurs_pct": "mean",
    "vpd_kpa": "mean",
    "et0_mm": "sum",
    "soil_moist_pct": "last",
}


def grid_dates(year: int, step: int = STEP_DAYS) -> pd.DatetimeIndex:
    start, end = (pd.Timestamp(f"{year}-{d}") for d in PREDICTION_WINDOW)
    return pd.date_range(start, end, freq=f"{step}D")


def assign_step(dates: pd.Series, grid: pd.DatetimeIndex, step: int = STEP_DAYS) -> pd.Series:
    """Grid date t whose step (t - step, t] contains each date, or NaT."""
    dates = pd.to_datetime(dates)
    idx = grid.searchsorted(dates, side="left")
    ends = pd.Series(pd.NaT, index=dates.index, dtype="datetime64[ns]")
    ok = idx < len(grid)
    ends[ok] = grid[idx[ok]]
    ends[ends - pd.Timedelta(days=step) >= dates] = pd.NaT
    return ends


def _base(field_ids: Sequence[str], grid: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "field_id": np.repeat(np.asarray(field_ids, dtype=object), len(grid)),
            "date": np.tile(grid.to_numpy(), len(field_ids)),
        }
    )


def _days_since(base: pd.DataFrame, obs_dates: pd.DataFrame) -> pd.Series:
    """Days from the latest observation on or before each grid date (NaN if none)."""
    if obs_dates.empty:
        return pd.Series(np.nan, index=base.index)
    left = base[["field_id", "date"]].reset_index().sort_values("date")
    right = obs_dates.assign(obs_date=obs_dates["date"]).sort_values("date")
    merged = pd.merge_asof(left, right[["field_id", "date", "obs_date"]], on="date", by="field_id")
    days = (merged["date"] - merged["obs_date"]).dt.days.astype("float64")
    return pd.Series(days.to_numpy(), index=merged["index"]).sort_index()


def _add_source(
    base: pd.DataFrame,
    obs: pd.DataFrame,
    values: Sequence[str],
    grid: pd.DatetimeIndex,
    prefix: str,
    suffix: str = "",
) -> pd.DataFrame:
    obs = obs.assign(date=pd.to_datetime(obs["date"])).sort_values("date")
    obs = obs.assign(step=assign_step(obs["date"], grid)).dropna(subset=["step"])
    latest = obs.groupby(["field_id", "step"], as_index=False).last()
    latest = latest.rename(columns={"step": "date_step"})[["field_id", "date_step", *values]]
    latest = latest.rename(columns={v: f"{v}{suffix}" for v in values})
    out = base.merge(
        latest, left_on=["field_id", "date"], right_on=["field_id", "date_step"], how="left"
    ).drop(columns="date_step")
    out[f"{prefix}_observed"] = out[f"{values[0]}{suffix}"].notna()
    return out


def build_grid(
    field_ids: Sequence[str],
    year: int,
    s2: pd.DataFrame,
    s1: pd.DataFrame,
    weather: pd.DataFrame,
    step: int = STEP_DAYS,
) -> pd.DataFrame:
    grid = grid_dates(year, step)
    out = _base(field_ids, grid)

    clear = s2[s2["clear_fraction"] >= S2_CLEAR_THRESHOLD].dropna(subset=["ndvi"])
    clear = clear.assign(date=pd.to_datetime(clear["date"]))
    out = _add_source(out, clear, S2_VALUES, grid, "s2")
    out["s2_days_since"] = _days_since(out, clear[["field_id", "date"]])

    s1 = s1.assign(date=pd.to_datetime(s1["date"]))
    for orbit, sfx in ORBIT_SUFFIX.items():
        part = s1[s1["orbit_state"] == orbit]
        out = _add_source(out, part, S1_VALUES, grid, f"s1_{sfx}", f"_{sfx}")
        out[f"s1_{sfx}_days_since"] = _days_since(out, part[["field_id", "date"]])

    w = weather.assign(date=pd.to_datetime(weather["date"])).sort_values("date")
    w = w.assign(step=assign_step(w["date"], grid, step)).dropna(subset=["step"])
    agg = w.groupby(["field_id", "step"]).agg({**WEATHER_AGG, "date": "count"})
    agg = agg.rename(columns={"date": "weather_days"}).reset_index()
    out = out.merge(agg.rename(columns={"step": "date"}), on=["field_id", "date"], how="left")
    out["weather_observed"] = out["weather_days"] == step
    out.insert(1, "year", year)
    return out.sort_values(["field_id", "date"]).reset_index(drop=True)
