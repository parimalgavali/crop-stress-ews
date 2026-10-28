"""Fit the Live spring risk model (US-22, ADR 0021) and save it as one joblib bundle.

Same recipe as ``export_predictions.py`` (US-08 logistic, Platt on validation, red/amber at
90 %/75 % validation specificity), but without the AMBAV features (ET0, soil moisture): AMBAV
is published monthly, so they are missing in Live. Reports the AUROC cost of dropping them.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from cropews.baselines import logistic_model
from cropews.config import HORIZONS_DAYS
from cropews.dataset import load_feature_table
from cropews.evaluation import threshold_at_specificity
from cropews.features import feature_columns

AMBAV_FEATURES = ("water_balance_30d", "soil_moist_pct")


def _fit(train, val, cols, target):  # type: ignore[no-untyped-def]
    model = logistic_model().fit(train[cols], train[target].astype(int))
    z = model.decision_function(val[cols]).reshape(-1, 1)
    platt = LogisticRegression().fit(z, val[target].astype(int))
    return model, platt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--out", type=Path, default=Path("models/risk_live.joblib"))
    parser.add_argument("--report", type=Path, default=Path("outputs/live_model.json"))
    args = parser.parse_args()

    data = load_feature_table(args.processed_dir)
    full = [c for c in feature_columns(data) if not c.startswith("onset_")]
    full = [c for c in full if c not in ("in_event", "split")]
    live = [c for c in full if c not in AMBAV_FEATURES]
    bundle: dict[str, object] = {"columns": live, "horizons": {}}
    report: dict[str, object] = {}
    for h in HORIZONS_DAYS:
        target = f"onset_{h}d"
        d = data.dropna(subset=[target])
        train, val = d[d["split"] == "train"], d[d["split"] == "validation"]
        row: dict[str, float] = {}
        for name, cols in (("full", full), ("live", live)):
            model, platt = _fit(train, val, cols, target)
            for split in ("validation", "test", "extra_check"):
                s = d[d["split"] == split]
                row[f"{name}/{split}"] = round(
                    float(roc_auc_score(s[target].astype(int), model.decision_function(s[cols]))), 3
                )
        risk = platt.predict_proba(model.decision_function(val[cols]).reshape(-1, 1))[:, 1]
        y = val[target].astype(int).to_numpy()
        bundle["horizons"][h] = {  # type: ignore[index]
            "model": model,
            "platt": platt,
            "red": threshold_at_specificity(y, risk, 0.90),
            "amber": threshold_at_specificity(y, risk, 0.75),
        }
        report[f"{h}d"] = row
        print(f"{h:>2}d", row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, args.out)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
