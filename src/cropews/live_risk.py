"""Live spring risk: 7/14/21-day traffic lights from 5 April (US-22, ADR 0021)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from cropews.data.grid import build_grid
from cropews.explain import contributions, level, top_reasons
from cropews.features import build_features
from cropews.labels import SENESCENCE_CUTOFF

SPRING_START = "04-05"


def spring_active(as_of: date) -> bool:
    """Forecasts start on 5 April and stop when even the 7-day horizon passes senescence."""
    start = date.fromisoformat(f"{as_of.year}-{SPRING_START}")
    end = date.fromisoformat(f"{as_of.year}-{SENESCENCE_CUTOFF}") - timedelta(days=7)
    return start <= as_of <= end


def load_bundle(path: Path | None) -> dict[str, Any] | None:
    return joblib.load(path) if path is not None and path.is_file() else None


def score_live(
    bundle: dict[str, Any],
    districts: pd.Series,
    s2: pd.DataFrame,
    s1: pd.DataFrame,
    daily: pd.DataFrame,
    as_of: date,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """``districts``: field_id -> district. Returns per-field risk cards and log rows."""
    grid = build_grid(list(districts.index), as_of.year, s2, s1, daily)
    grid = grid[grid["date"] <= pd.Timestamp(as_of)].assign(
        district=lambda g: g["field_id"].map(districts)
    )
    if grid.empty:
        return {}, []
    feats = build_features(grid)
    last = feats.sort_values("date").groupby("field_id").tail(1).reset_index(drop=True)
    x = last[bundle["columns"]]
    cards: dict[str, dict[str, Any]] = {
        r.field_id: {
            "field_id": r.field_id,
            "year": as_of.year,
            "date": r.date.date().isoformat(),
            "district": r.district,
            "horizons": [],
        }
        for r in last.itertuples(index=False)
    }
    cutoff = pd.Timestamp(f"{as_of.year}-{SENESCENCE_CUTOFF}")
    rows: list[dict[str, Any]] = []
    for h, b in sorted(bundle["horizons"].items()):
        z = b["model"].decision_function(x).reshape(-1, 1)
        risk = b["platt"].predict_proba(z)[:, 1]
        lvl = level(risk, b["amber"], b["red"])
        reasons = top_reasons(contributions(b["model"], x))
        for i, fid in enumerate(last["field_id"]):
            # Like the replay export: no outcome label exists past senescence (labels.py).
            if last["date"].iat[i] + pd.Timedelta(days=int(h)) > cutoff:
                continue
            r = round(float(risk[i]), 4)
            cards[fid]["horizons"].append(
                {"days": int(h), "risk": r, "level": str(lvl[i]), "reasons": reasons[i]}
            )
            rows.append(
                {
                    "field_id": fid,
                    "date": cards[fid]["date"],
                    "horizon_days": int(h),
                    "risk": r,
                    "level": str(lvl[i]),
                }
            )
    return {k: c for k, c in cards.items() if c["horizons"]}, rows
