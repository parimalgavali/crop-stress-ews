"""Train and evaluate the US-09 sequence models and ablations with the ADR 0008 protocol.

Each config is a seed ensemble trained on SPLITS["train"] with early stopping on validation.
The config is chosen on validation AUROC only; its scores are Platt-calibrated on validation,
the alarm threshold is frozen at 90% validation specificity, and test/extra_check are reported
once with field-bootstrap CIs.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from cropews.config import HORIZONS_DAYS, SPLITS
from cropews.evaluation import bootstrap_ci, metrics, threshold_at_specificity
from cropews.seqmodels import fit, predict_logits
from cropews.sequence import (
    CHANNEL_GROUPS,
    TARGETS,
    add_peer_channels,
    channels,
    fit_scaler,
    model_inputs,
    row_index,
    to_sequences,
)

GRID_NAME = re.compile(r"grid_(?P<district>.+)_(?P<year>\d{4})\.parquet")
ALL = tuple(CHANNEL_GROUPS)
FULL = 24
CONFIGS: dict[str, tuple[str, int, tuple[str, ...]]] = {
    "grud": ("grud", FULL, ALL),
    "lstm": ("lstm", FULL, ALL),
    "grud_window30d": ("grud", 6, ALL),
    "grud_window60d": ("grud", 12, ALL),
    "grud_no_s1": ("grud", FULL, ("s2", "weather")),
    "grud_no_weather": ("grud", FULL, ("s2", "s1")),
}


def load(processed: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(processed.glob("grid_*.parquet")):
        m = GRID_NAME.fullmatch(path.name)
        labels = path.with_name(path.name.replace("grid_", "labels_"))
        if not m or not labels.exists():
            continue
        grid = pd.read_parquet(path).assign(district=m["district"])
        lab = pd.read_parquet(labels)[["field_id", "year", "date", *TARGETS]]
        frames.append(grid.merge(lab, on=["field_id", "year", "date"], how="left"))
    if not frames:
        raise SystemExit(f"no grid/label pairs in {processed}")
    return add_peer_channels(pd.concat(frames, ignore_index=True))


def ensemble_logits(arch, inputs, seeds):  # type: ignore[no-untyped-def]
    models = [fit(arch, inputs["train"], inputs["validation"], seed=s) for s in range(seeds)]
    return {
        split: np.mean([predict_logits(mdl, data) for mdl in models], axis=0)
        for split, data in inputs.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--out", type=Path, default=Path("outputs/sequence.json"))
    parser.add_argument("--configs", nargs="+", default=list(CONFIGS), choices=list(CONFIGS))
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--bootstrap", type=int, default=500)
    args = parser.parse_args()

    data = load(args.processed_dir)
    split_of = {y: name for name, years in SPLITS.items() for y in years}
    results: dict[str, dict[str, object]] = {}
    scored: dict[str, dict[str, np.ndarray]] = {}
    index: dict[str, pd.DataFrame] = {}
    for name in args.configs:
        arch, w, groups = CONFIGS[name]
        seqs = {
            s: to_sequences(data[data["year"].map(split_of) == s], channels(groups))
            for s in SPLITS
            if data["year"].map(split_of).eq(s).any()
        }
        mean, sd = fit_scaler(seqs["train"].x)
        inputs = {s: model_inputs(q, mean, sd, w) for s, q in seqs.items()}
        index = {s: row_index(q) for s, q in seqs.items()}
        scored[name] = ensemble_logits(arch, inputs, args.seeds)
        val_auc = {}
        for k, h in enumerate(HORIZONS_DAYS):
            y = inputs["validation"]["y"][:, k]
            ok = ~np.isnan(y)
            val_auc[f"{h}d"] = float(roc_auc_score(y[ok], scored[name]["validation"][ok, k]))
        results[name] = {"validation_auroc": val_auc, "inputs": inputs}
        print(
            f"{name:<16} validation AUROC " + " ".join(f"{k} {v:.3f}" for k, v in val_auc.items())
        )

    best = max(args.configs, key=lambda n: np.mean(list(results[n]["validation_auroc"].values())))
    print(f"selected on validation: {best}")
    report: dict[str, object] = {
        "validation_auroc": {n: r["validation_auroc"] for n, r in results.items()},
        "selected": best,
        "test": {},
    }
    for name in args.configs:
        inputs = results[name]["inputs"]
        per_h: dict[str, object] = {}
        for k, h in enumerate(HORIZONS_DAYS):
            val_y = inputs["validation"]["y"][:, k]
            ok = ~np.isnan(val_y)
            platt = LogisticRegression().fit(scored[name]["validation"][ok, k : k + 1], val_y[ok])
            prob = {s: platt.predict_proba(z[:, k : k + 1])[:, 1] for s, z in scored[name].items()}
            thr = threshold_at_specificity(val_y[ok], prob["validation"][ok])
            entry: dict[str, object] = {"threshold": thr}
            for split in ("test", "extra_check"):
                if split not in inputs:
                    continue
                y = inputs[split]["y"][:, k]
                ev = (
                    index[split].assign(y=y, score=prob[split])[~np.isnan(y)].reset_index(drop=True)
                )
                if ev["y"].nunique() < 2:
                    continue
                ev["y"] = ev["y"].astype(int)
                m = metrics(ev, thr)
                m["auroc_ci"] = bootstrap_ci(
                    ev, lambda s, t=thr: metrics(s, t)["auroc"], n=args.bootstrap
                )
                m["n_rows"], m["n_fields"] = len(ev), ev["field_id"].nunique()
                entry[split] = m
            per_h[f"{h}d"] = entry
            t = entry.get("test")
            if isinstance(t, dict):
                lo, hi = t["auroc_ci"]
                print(
                    f"{h:>2}d {name:<16} AUROC {t['auroc']:.3f} [{lo:.3f}–{hi:.3f}] "
                    f"AUPRC {t['auprc']:.3f} (prev {t['prevalence']:.3f}) Brier {t['brier']:.3f} "
                    f"sens {t['sensitivity']:.2f} FA/100 {t['false_alarms_per_100_fields']:.0f}"
                )
        report["test"][name] = per_h  # type: ignore[index]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=float))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
