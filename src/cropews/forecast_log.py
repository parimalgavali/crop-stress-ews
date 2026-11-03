"""Prospective forecast log and scoreboard (US-20, ADR 0020).

Each live run appends its forecasts, stamped with the run time, to a log kept on the
``forecast-log`` branch. A forecast is scored only once its window has passed.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

KEY = ["field_id", "date", "horizon_days"]
COLUMNS = [*KEY, "risk", "level", "issued_at", "model_version"]


def append_log(path: Path, entries: pd.DataFrame) -> pd.DataFrame:
    """Append ``entries``; a forecast already in the log is never overwritten."""
    if "model_version" not in entries:
        entries = entries.assign(model_version="")
    new = entries.assign(date=pd.to_datetime(entries["date"]).dt.strftime("%Y-%m-%d"))[COLUMNS]
    if path.exists():
        old = pd.read_csv(path, dtype={"field_id": str})
        new = pd.concat([old, new], ignore_index=True).drop_duplicates(KEY, keep="first")
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(path, index=False)
    return new


SCOREBOARD_SCHEMA = 2


def outcomes_long(
    targets: pd.DataFrame, horizons: tuple[int, ...], keep_nan: bool = False
) -> pd.DataFrame:
    """``onset_<h>d`` columns -> rows of (field_id, date, horizon_days, y).

    ``keep_nan`` retains rows whose outcome is unobservable (label policy returned NaN) so the
    scoreboard can report them separately from still-pending outcomes (spec 8.4).
    """
    out = pd.concat(
        targets[["field_id", "date"]].assign(horizon_days=h, y=targets[f"onset_{h}d"])
        for h in horizons
    )
    return out if keep_nan else out.dropna(subset=["y"])


def scoreboard(log: pd.DataFrame, outcomes: pd.DataFrame, today: date) -> dict[str, Any]:
    """Per horizon: issued = pending + scored + no_outcome (window passed, no label)."""
    log = log.assign(date=pd.to_datetime(log["date"]), field_id=log["field_id"].astype(str))
    out = outcomes.assign(
        date=pd.to_datetime(outcomes["date"]), field_id=outcomes["field_id"].astype(str)
    )
    due = log["date"] + pd.to_timedelta(log["horizon_days"], unit="D") <= pd.Timestamp(today)
    # Review finding 4.3: a forecast issued after its feature origin is "stale" — part of its
    # window already elapsed at issuance, so it can never earn outcome credit (aligned-schedule
    # policy: only forecasts issued on their origin day are scored). Same-day issuance counts as
    # aligned; intraday issuance lag is a documented limit.
    issued_day = pd.to_datetime(log["issued_at"], utc=True, errors="coerce").dt.date
    stale = (issued_day > log["date"].dt.date).fillna(False)
    evaluable = log[due & ~stale]
    # Outcome rows with a NaN y exist but are permanently unobservable (spec 8.4); an absent
    # row means the outcome is still pending. Score only rows with a real label.
    merged = evaluable.merge(out, on=KEY, how="left", indicator=True)
    scored = merged[merged["y"].notna()]
    unobs = merged[(merged["_merge"] == "both") & merged["y"].isna()]
    pendo = merged[merged["_merge"] == "left_only"]
    board: dict[str, Any] = {
        "as_of": today.isoformat(),
        "schema_version": SCOREBOARD_SCHEMA,
        "horizons": {},
    }
    for h, g in log.groupby("horizon_days"):
        s = scored[scored["horizon_days"] == h]
        n_unobs = int((unobs["horizon_days"] == h).sum())
        n_pendo = int((pendo["horizon_days"] == h).sum())
        y, red = s["y"].astype(int), s["level"] == "red"
        both = y.nunique() == 2
        # Persistence baseline: each scored forecast's risk from the same field's previous
        # logged forecast at this horizon (spec 8.4). Only rows with a prior forecast count.
        prev_risk = g.sort_values("date").set_index(KEY)["risk"].groupby(level="field_id").shift(1)
        s_prev = s.join(prev_risk.rename("prev_risk"), on=KEY).dropna(subset=["prev_risk"])
        both_prev = len(s_prev) and s_prev["y"].astype(int).nunique() == 2
        board["horizons"][str(int(h))] = {
            "issued": int(len(g)),
            "eligible": int((~stale[g.index]).sum()),
            "withheld": int(stale[g.index].sum()),
            "pending": int((~due[g.index]).sum()),
            "evaluated": int(len(s)),
            "unobservable": n_unobs,
            "pending_outcome": n_pendo,
            "scored": int(len(s)),
            "no_outcome": int(due[g.index].sum() - len(s)),
            "stale_origin": int(stale[g.index].sum()),
            "onsets": int(y.sum()),
            "auroc": round(float(roc_auc_score(y, s["risk"])), 3) if both else None,
            "auroc_persistence": (
                round(float(roc_auc_score(s_prev["y"].astype(int), s_prev["prev_risk"])), 3)
                if both_prev
                else None
            ),
            "red_hits": int((red & (y == 1)).sum()),
            "red_false": int((red & (y == 0)).sum()),
            "missed": int((~red & (y == 1)).sum()),
            "first_issued": None if g.empty else str(np.min(g["issued_at"])),
        }
    return board
