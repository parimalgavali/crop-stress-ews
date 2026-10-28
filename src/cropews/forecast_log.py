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
COLUMNS = [*KEY, "risk", "level", "issued_at"]


def append_log(path: Path, entries: pd.DataFrame) -> pd.DataFrame:
    """Append ``entries``; a forecast already in the log is never overwritten."""
    new = entries.assign(date=pd.to_datetime(entries["date"]).dt.strftime("%Y-%m-%d"))[COLUMNS]
    if path.exists():
        old = pd.read_csv(path, dtype={"field_id": str})
        new = pd.concat([old, new], ignore_index=True).drop_duplicates(KEY, keep="first")
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(path, index=False)
    return new


def outcomes_long(targets: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    """``onset_<h>d`` columns -> rows of (field_id, date, horizon_days, y)."""
    return pd.concat(
        targets[["field_id", "date"]].assign(horizon_days=h, y=targets[f"onset_{h}d"])
        for h in horizons
    ).dropna(subset=["y"])


def scoreboard(log: pd.DataFrame, outcomes: pd.DataFrame, today: date) -> dict[str, Any]:
    """Per horizon: forecasts scored (window passed and outcome known) vs still pending."""
    log = log.assign(date=pd.to_datetime(log["date"]), field_id=log["field_id"].astype(str))
    out = outcomes.assign(
        date=pd.to_datetime(outcomes["date"]), field_id=outcomes["field_id"].astype(str)
    )
    due = log["date"] + pd.to_timedelta(log["horizon_days"], unit="D") <= pd.Timestamp(today)
    scored = log[due].merge(out, on=KEY, how="inner")
    board: dict[str, Any] = {"as_of": today.isoformat(), "horizons": {}}
    for h, g in log.groupby("horizon_days"):
        s = scored[scored["horizon_days"] == h]
        y, red = s["y"].astype(int), s["level"] == "red"
        both = y.nunique() == 2
        board["horizons"][str(int(h))] = {
            "issued": int(len(g)),
            "pending": int((~due[g.index]).sum()),
            "scored": int(len(s)),
            "onsets": int(y.sum()),
            "auroc": round(float(roc_auc_score(y, s["risk"])), 3) if both else None,
            "red_hits": int((red & (y == 1)).sum()),
            "red_false": int((red & (y == 0)).sum()),
            "missed": int((~red & (y == 1)).sum()),
            "first_issued": None if g.empty else str(np.min(g["issued_at"])),
        }
    return board
