"""Error analysis of the exported traffic lights on the 2024 test season (US-12).

Joins ``predictions.parquet`` (from ``export_predictions.py``) to labels, field size and the
Sentinel-2 cloud gap, then reports red-alarm misses and false alarms by district, field size and
cloud gap, plus how many days before onset the first red alarm came.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cropews.dataset import load_feature_table
from cropews.errors import add_strata, error_table, lead_times


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--outputs-dir", type=Path, default=Path("data/outputs"))
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--level", default="red", choices=("red", "amber"))
    args = parser.parse_args()

    data = load_feature_table(args.processed_dir)
    data = data[data["year"] == args.year]
    preds = pd.read_parquet(args.outputs_dir / "predictions.parquet")
    preds = preds[preds["year"] == args.year]
    fields = pd.read_parquet(
        args.outputs_dir / "fields.geoparquet", columns=["field_id", "year", "area_ha"]
    )
    keys = ["field_id", "year", "date"]
    base = data[[*keys, "district", "s2_days_since", "onset_7d", "onset_14d", "onset_21d"]]
    base = add_strata(base.merge(fields, on=["field_id", "year"]))

    alarm = preds
    if args.level == "amber":  # amber-or-red counts as an alarm
        alarm = preds.assign(level=preds["level"].replace("amber", "red"))
    for h in sorted(preds["horizon_days"].unique()):
        p = alarm[alarm["horizon_days"] == h][[*keys, "level"]]
        f = base.merge(p, on=keys).dropna(subset=[f"onset_{h}d"])
        f = f.assign(y=f[f"onset_{h}d"].astype(int))
        print(f"\n=== {h}-day horizon, {args.year}, alarm = {args.level} ===")
        for by in ("district", "size_bin", "cloud_gap"):
            t = error_table(f, by)
            print(t.round(3).to_string(), "\n")

    lt = lead_times(data[["field_id", "year", "date", "in_event"]], alarm)
    warned = lt["lead_days"].notna()
    print(f"=== lead time ({args.level} alarm in the 21 days before onset) ===")
    print(f"onsets: {len(lt)}, warned: {warned.sum()} ({warned.mean():.0%})")
    if warned.any():
        print(lt.loc[warned, "lead_days"].describe().round(1).to_string())


if __name__ == "__main__":
    main()
