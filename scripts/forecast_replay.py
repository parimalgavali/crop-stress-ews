"""Replay a past season through the forecast log as if live (US-20, ADR 0020).

Logs the precomputed forecasts of ``--year`` run by run (every 5 days), scores the log at
several dates and checks the final scoreboard against the offline AUROC.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import timedelta
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score

from cropews.config import HORIZONS_DAYS
from cropews.dataset import load_feature_table
from cropews.forecast_log import append_log, outcomes_long, scoreboard


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictions", type=Path, default=Path("data/outputs/predictions.parquet")
    )
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--out", type=Path, default=Path("outputs/forecast_replay.json"))
    args = parser.parse_args()

    preds = pd.read_parquet(args.predictions)
    preds = preds[preds["year"] == args.year].assign(field_id=lambda d: d["field_id"].astype(str))
    data = load_feature_table(args.processed_dir)
    data = data[data["year"] == args.year].assign(field_id=lambda d: d["field_id"].astype(str))
    outcomes = outcomes_long(data, HORIZONS_DAYS)

    runs = sorted(preds["date"].dt.date.unique())
    report: dict[str, object] = {
        "year": args.year,
        "runs": len(runs),
        "levels": sorted(preds["level"].unique()),
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "log.csv"
        for run in runs:
            batch = preds[preds["date"].dt.date == run]
            log = append_log(path, batch.assign(issued_at=f"{run}T06:00:00Z"))
        checks = [runs[0] + timedelta(days=30), runs[len(runs) // 2], runs[-1] + timedelta(days=21)]
        report["boards"] = [scoreboard(log, outcomes, d) for d in checks]
    offline = {}
    for h in HORIZONS_DAYS:
        m = preds[preds["horizon_days"] == h].merge(
            outcomes[outcomes["horizon_days"] == h], on=["field_id", "date", "horizon_days"]
        )
        offline[str(h)] = round(float(roc_auc_score(m["y"].astype(int), m["risk"])), 3)
    report["offline_auroc"] = offline
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1, default=str))
    final = report["boards"][-1]["horizons"]  # type: ignore[index]
    for h in offline:
        print(h, final[h], "offline", offline[h])


if __name__ == "__main__":
    main()
