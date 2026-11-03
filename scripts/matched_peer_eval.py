"""Matched-peer experiment (US-67, dossier 6.1/P2, ADR 0063).

The risk model compares each field with the district-wide peer median on the same date.
Here the peer group is narrowed to fields in the same soil water-holding class (the same
nfk_mm classes shown on the Live cards: <90 little, <200 medium, else lots), still within
the district, with a minimum support of 5 matched peers falling back to the district median.

Trains logistic + lightgbm with district peers vs soil-matched peers and compares AUROC on
2022 (validation), 2024 (test) and 2025 (extra check). Adopted only if it helps on 2022.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from cropews.baselines import lightgbm_model, logistic_model
from cropews.config import HORIZONS_DAYS, SPLITS
from cropews.evaluation import bootstrap_ci
from cropews.features import build_features, feature_columns

GRID_NAME = re.compile(r"grid_(?P<district>.+)_(?P<year>\d{4})\.parquet")
MIN_PEERS = 5


def water_hold(nfk: float) -> str:
    return "little" if nfk < 90 else ("medium" if nfk < 200 else "lots")


def load_variants(processed: Path, soil: Path) -> dict[str, pd.DataFrame]:
    soils = pd.read_parquet(soil)[["field_id", "nfk_mm"]].dropna()
    soils["peer_class"] = soils["district_class"] = soils["nfk_mm"].map(water_hold)
    out: dict[str, list[pd.DataFrame]] = {"district": [], "soil_matched": []}
    for path in sorted(processed.glob("grid_*.parquet")):
        m = GRID_NAME.fullmatch(path.name)
        labels = path.with_name(path.name.replace("grid_", "labels_"))
        if not m or not labels.exists():
            continue
        district = m["district"]
        grid = pd.read_parquet(path).assign(district=district)
        lab = pd.read_parquet(labels)
        out["district"].append(build_features(grid).merge(lab, on=["field_id", "year", "date"]))
        matched = grid.merge(
            soils.assign(peer_class=district + "|" + soils["peer_class"])[
                ["field_id", "peer_class"]
            ],
            on="field_id",
            how="left",
        )
        matched["peer_class"] = matched["peer_class"].fillna(district + "|unknown")
        feats = build_features(matched, peer_key="peer_class", min_peers=MIN_PEERS)
        out["soil_matched"].append(
            feats.drop(columns=["peer_class"]).merge(lab, on=["field_id", "year", "date"])
        )
    return {k: pd.concat(v, ignore_index=True) for k, v in out.items()}


def _auc(frame: pd.DataFrame, n: int) -> dict[str, object]:
    return {
        "auroc": float(roc_auc_score(frame["y"], frame["score"])),
        "ci": bootstrap_ci(frame, lambda s: float(roc_auc_score(s["y"], s["score"])), n=n),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--soil", type=Path, default=Path("data/interim/soil.parquet"))
    parser.add_argument("--out", type=Path, default=Path("outputs/matched_peer_eval.json"))
    parser.add_argument("--bootstrap", type=int, default=300)
    args = parser.parse_args()

    variants = load_variants(args.processed_dir, args.soil)
    split = {y: name for name, years in SPLITS.items() for y in years}
    report: dict[str, object] = {"min_peers": MIN_PEERS, "peer_class": "district|nfk_class"}
    for h in HORIZONS_DAYS:
        t = f"onset_{h}d"
        rows: dict[str, object] = {}
        for name, make in (("logistic", logistic_model), ("lightgbm", lightgbm_model)):
            res: dict[str, object] = {}
            for label, data in variants.items():
                d = data.dropna(subset=[t]).assign(y=lambda x, t=t: x[t].astype(int))
                d = d.assign(split=d["year"].map(split))
                cols = feature_columns(
                    d.drop(
                        columns=[
                            c
                            for c in d
                            if c.startswith(("onset_", "in_event", "split")) or c == "y"
                        ]
                    )
                )
                tr = d[d.split == "train"]
                model = make().fit(tr[cols], tr["y"])
                for s in ("validation", "test", "extra_check"):
                    ev = d[d.split == s]
                    res[f"{label}/{s}"] = _auc(
                        ev.assign(score=model.predict_proba(ev[cols])[:, 1]), args.bootstrap
                    )
            rows[name] = res
            print(
                f"{h:>2}d {name:<9} " + "  ".join(f"{k} {v['auroc']:.3f}" for k, v in res.items())
            )  # type: ignore[index]
        report[f"{h}d"] = rows
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=lambda v: np.asarray(v).tolist()))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
