"""Held-season scouting-queue benchmark (spec 8.2): top-k event capture vs baselines.

Ranks fields by the logged 14-day risk each date and measures the share of in-event target
rows inside a top-k queue, against persistence (yesterday's ranking) and random order.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cropews.scouting import queue_capture


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preds", type=Path, default=Path("data/outputs/predictions.parquet"))
    p.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    p.add_argument("--horizon", type=int, default=14)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--out", type=Path, default=Path("outputs/scouting_eval.json"))
    args = p.parse_args()

    preds = pd.read_parquet(args.preds)
    preds = preds[preds["horizon_days"] == args.horizon]
    labels = pd.concat(
        [
            pd.read_parquet(f)[["field_id", "year", "date", f"onset_{args.horizon}d"]]
            for f in sorted(args.processed_dir.glob("labels_*.parquet"))
        ]
    ).rename(columns={f"onset_{args.horizon}d": "in_event"})
    labels["in_event"] = labels["in_event"].fillna(0).astype(bool)
    out = {}
    for year, g in preds.groupby("year"):
        t = labels[labels["year"] == year].merge(
            g[["field_id", "date"]], on=["field_id", "date"], how="inner"
        )
        out[str(year)] = queue_capture(
            g[["field_id", "date", "risk"]],
            t[["field_id", "date", "in_event"]],
            args.horizon,
            args.k,
        )
    args.out.parent.mkdir(exist_ok=True, parents=True)
    args.out.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
