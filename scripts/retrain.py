"""Champion/challenger retraining of the Live spring risk model (US-28, ADR 0026).

Example (yearly, once a new season's labels exist):
    python scripts/retrain.py --holdout 2026 --add 2025
The challenger trains on the US-08 train seasons plus ``--add``. Calibration and thresholds stay
on the 2022 validation season. Both models are scored on ``--holdout``. The challenger is only
written if ``decide`` promotes it; publishing it (release + models.sha256) is a manual step.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib

from cropews.dataset import load_feature_table
from cropews.retrain import decide, fit_bundle, holdout_auroc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--champion", type=Path, default=Path("models/risk_live.joblib"))
    parser.add_argument("--holdout", type=int, required=True, help="season neither model saw")
    parser.add_argument("--add", type=int, nargs="+", required=True, help="seasons added to train")
    parser.add_argument("--out", type=Path, default=Path("models/risk_live_challenger.joblib"))
    parser.add_argument("--report", type=Path, default=Path("outputs/retrain.json"))
    args = parser.parse_args()

    data = load_feature_table(args.processed_dir)
    if args.holdout in args.add or args.holdout in set(data.loc[data["split"] == "train", "year"]):
        parser.error("the holdout season must not be used for training")
    champion = joblib.load(args.champion)
    train = data[(data["split"] == "train") | data["year"].isin(args.add)]
    challenger = fit_bundle(train, data[data["split"] == "validation"], champion["columns"])
    holdout = data[data["year"] == args.holdout]
    report = {
        "holdout": args.holdout,
        "added": args.add,
        "train_seasons": sorted(int(y) for y in train["year"].unique()),
        "champion": holdout_auroc(champion, holdout),
        "challenger": holdout_auroc(challenger, holdout),
    }
    report |= decide(report["champion"], report["challenger"])
    print(json.dumps(report, indent=1))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=1))
    if report["promote"]:
        joblib.dump(challenger, args.out)
        print(f"promote: wrote {args.out}; publish as a new risk-vN release, update models.sha256")


if __name__ == "__main__":
    main()
