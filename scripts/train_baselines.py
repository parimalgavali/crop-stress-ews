"""Train and evaluate the US-08 baselines with the fixed protocol (ADR 0008).

Train on SPLITS["train"], choose each model's alarm threshold at 90% specificity on the
validation season, report on the test season (and extra_check) with field-bootstrap CIs.
"""

from __future__ import annotations

import argparse
import json
import re
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

from cropews.baselines import lightgbm_model, logistic_model, persistence_score, weather_rule_score
from cropews.config import HORIZONS_DAYS, SPLITS
from cropews.evaluation import bootstrap_ci, metrics, threshold_at_specificity
from cropews.features import build_features, feature_columns

RULES = {"persistence": persistence_score, "weather_rule": weather_rule_score}
GRID_NAME = re.compile(r"grid_(?P<district>.+)_(?P<year>\d{4})\.parquet")


def load(processed: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(processed.glob("grid_*.parquet")):
        m = GRID_NAME.fullmatch(path.name)
        labels = path.with_name(path.name.replace("grid_", "labels_"))
        if not m or not labels.exists():
            continue
        grid = pd.read_parquet(path).assign(district=m["district"])
        feats = build_features(grid)
        frames.append(feats.merge(pd.read_parquet(labels), on=["field_id", "year", "date"]))
    if not frames:
        raise SystemExit(f"no grid/label pairs in {processed}")
    return pd.concat(frames, ignore_index=True)


def _predict(frame: pd.DataFrame, name: str, fitted: dict, cols: list[str]) -> np.ndarray:
    if name in RULES:
        return RULES[name](frame).to_numpy()
    return fitted[name].predict_proba(frame[cols])[:, 1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--out", type=Path, default=Path("outputs/baselines.json"))
    parser.add_argument("--bootstrap", type=int, default=500)
    args = parser.parse_args()

    data = load(args.processed_dir)
    cols = feature_columns(data.drop(columns=[c for c in data if c.startswith("onset_")]))
    cols = [c for c in cols if c != "in_event"]
    split = {y: name for name, years in SPLITS.items() for y in years}
    data["split"] = data["year"].map(split)
    print(data.groupby("split")[["field_id"]].nunique().T.to_string())

    results: dict[str, dict[str, dict[str, object]]] = {}
    for h in HORIZONS_DAYS:
        target = f"onset_{h}d"
        d = data.dropna(subset=[target]).assign(y=lambda x, t=target: x[t].astype(int))
        train, val = d[d.split == "train"], d[d.split == "validation"]
        fitted = {
            name: model.fit(train[cols], train["y"])
            for name, model in (("logistic", logistic_model()), ("lightgbm", lightgbm_model()))
        }
        results[f"{h}d"] = {}
        for name in [*RULES, *fitted]:
            predict = partial(_predict, name=name, fitted=fitted, cols=cols)
            thr = threshold_at_specificity(val["y"].to_numpy(), predict(val))
            entry: dict[str, object] = {"threshold": thr}
            for split_name in ("test", "extra_check"):
                ev = d[d.split == split_name]
                ev = ev.assign(score=predict(ev))
                if ev.empty or ev["y"].nunique() < 2:
                    continue
                m = metrics(ev, thr)
                m["auroc_ci"] = bootstrap_ci(
                    ev, lambda s, t=thr: metrics(s, t)["auroc"], n=args.bootstrap
                )
                m["auprc_ci"] = bootstrap_ci(
                    ev, lambda s, t=thr: metrics(s, t)["auprc"], n=args.bootstrap
                )
                m["n_rows"], m["n_fields"] = len(ev), ev["field_id"].nunique()
                entry[split_name] = m
            results[f"{h}d"][name] = entry
            test = entry.get("test", {})
            if isinstance(test, dict) and test:
                print(
                    f"{h:>2}d {name:<13} AUROC {test['auroc']:.3f} {test['auroc_ci']} "
                    f"AUPRC {test['auprc']:.3f} (prev {test['prevalence']:.3f}) "
                    f"sens {test['sensitivity']:.2f} "
                    f"FA/100 {test['false_alarms_per_100_fields']:.0f}"
                )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, default=float))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
