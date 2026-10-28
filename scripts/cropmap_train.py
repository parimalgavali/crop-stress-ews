"""Train and evaluate the in-season winter-wheat map on past Europe-LAND seasons (ADR 0018).

Reads ``--crops arable --window winter`` extractions (s1wa, s2wa, crops_*.parquet). One model per
cutoff (1 Dec, 1 Feb, 1 Apr). Model choice uses 2022 only; 2024 is the held-out test season and
2025 an extra check.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cropews.cropmap import CUTOFF_MONTHS, features, per_group_scores, save_model, targets

SPLITS = {"train": (2020, 2021, 2023), "validation": (2022,), "test": (2024,), "extra": (2025,)}


def load(root: Path) -> dict[str, pd.DataFrame]:
    s1 = pd.concat(pd.read_parquet(p) for p in sorted((root / "s1wa").glob("s1_*.parquet")))
    s2 = pd.concat(pd.read_parquet(p) for p in sorted((root / "s2wa").glob("s2_*.parquet")))
    crops = pd.concat(
        pd.read_parquet(p) for p in sorted((root / "s2wa").glob("crops_*.parquet"))
    ).drop_duplicates(["field_id", "year"])
    return {
        cutoff: targets(crops).merge(features(s1, s2, months), on=["field_id", "year"])
        for cutoff, months in CUTOFF_MONTHS.items()
    }


def _models() -> dict[str, Any]:
    from lightgbm import LGBMClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return {
        "logistic": lambda: make_pipeline(
            SimpleImputer(), StandardScaler(), LogisticRegression(max_iter=2000, C=0.5)
        ),
        "lightgbm": lambda: LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=20,
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.8,
            verbose=-1,
            random_state=0,
        ),
    }


def run(data: pd.DataFrame, cutoff: str, model_dir: Path) -> dict[str, object]:
    from sklearn.metrics import roc_auc_score

    cols = [c for c in data.columns if c.startswith(("s1_", "s2_"))]
    split = {y: s for s, ys in SPLITS.items() for y in ys}
    data = data.assign(split=data["year"].map(split)).dropna(subset=["split"])
    print(f"\n=== cutoff {cutoff}: {len(cols)} features")
    if cutoff == "apr":
        print(data.groupby("split")[["y_wheat", "y_cereal"]].agg(["size", "sum"]).to_string())
    train = data[data["split"] == "train"]
    val = data[data["split"] == "validation"]
    report: dict[str, object] = {}
    for target in ("y_wheat", "y_cereal"):
        fitted = {n: make().fit(train[cols], train[target]) for n, make in _models().items()}
        val_auc = {
            n: float(roc_auc_score(val[target], m.predict_proba(val[cols])[:, 1]))
            for n, m in fitted.items()
        }
        best = max(val_auc, key=val_auc.__getitem__)
        print(f"\n{cutoff} {target}: validation AUROC {val_auc} -> {best}")
        out: dict[str, object] = {"validation_auroc": val_auc, "model": best}
        for s in ("validation", "test", "extra"):
            part = data[data["split"] == s].reset_index(drop=True)
            prob = fitted[best].predict_proba(part[cols])[:, 1]
            table = per_group_scores(part, prob, target, "district")
            auc = float(roc_auc_score(part[target], prob))
            print(f"{s}: AUROC {auc:.3f}\n{table.round(2).to_string(index=False)}")
            out[s] = {"auroc": auc, "per_district": table.to_dict(orient="records")}
            if s == "test":
                flagged = part.assign(flag=prob >= 0.5)
                mix = flagged.groupby("EC_hcat_n")["flag"].agg(["size", "sum"])
                mix = mix.rename(columns={"size": "parcels", "sum": "flagged"})
                mix = mix.sort_values("parcels", ascending=False).head(10)
                print(f"test parcels flagged by declared crop:\n{mix.to_string()}")
                out["test_flagged_by_crop"] = mix.reset_index().to_dict(orient="records")
        report[target] = out
        save_model(model_dir / f"cropmap_{target}_{cutoff}.joblib", fitted[best], cols, 0.5)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interim", type=Path, default=Path("data/interim"))
    parser.add_argument("--out", type=Path, default=Path("data/processed/cropmap_metrics.json"))
    parser.add_argument("--models", type=Path, default=Path("models"))
    args = parser.parse_args()

    report = {cutoff: run(d, cutoff, args.models) for cutoff, d in load(args.interim).items()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=lambda v: np.asarray(v).item()))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
