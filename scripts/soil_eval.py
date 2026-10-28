"""Does BK50 soil help the risk model? (US-33, ADR 0030)

Reads soil for every training field (cached in data/interim/soil.parquet), then trains with and
without ``SOIL_FEATURES`` on the training years and compares AUROC on 2022 (validation), 2024
(test) and 2025 (extra check). Adopted only if it helps on 2022 (ADR 0008).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from train_baselines import load

from cropews.baselines import lightgbm_model, logistic_model
from cropews.config import HORIZONS_DAYS, SPLITS
from cropews.data.soil import SOIL_FEATURES, field_soils
from cropews.evaluation import bootstrap_ci
from cropews.features import feature_columns


def soils(data: pd.DataFrame, iacs: Path, cache: Path) -> pd.DataFrame:
    if cache.exists():
        return pd.read_parquet(cache)
    frames = []
    for year, ids in data.groupby("year")["field_id"].unique().items():
        f = gpd.read_parquet(
            iacs / f"GSA-DE_NRW-{year}.geoparquet", columns=["field_id", "geometry"]
        )
        frames.append(f[f["field_id"].isin(set(ids))])
    fields = pd.concat(frames).drop_duplicates("field_id")
    out = field_soils(gpd.GeoDataFrame(fields, crs=frames[0].crs))
    cache.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(cache, index=False)
    return out


def _auc(frame: pd.DataFrame, n: int) -> dict[str, object]:
    return {
        "auroc": float(roc_auc_score(frame["y"], frame["score"])),
        "ci": bootstrap_ci(frame, lambda s: float(roc_auc_score(s["y"], s["score"])), n=n),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--iacs", type=Path, default=Path("data/raw/iacs"))
    parser.add_argument("--cache", type=Path, default=Path("data/interim/soil.parquet"))
    parser.add_argument("--out", type=Path, default=Path("outputs/soil_eval.json"))
    parser.add_argument("--bootstrap", type=int, default=300)
    args = parser.parse_args()

    data = load(args.processed_dir)
    base = feature_columns(data.drop(columns=[c for c in data if c.startswith("onset_")]))
    base = [c for c in base if c != "in_event"]
    soil = soils(data, args.iacs, args.cache)
    fields = data[["field_id"]].drop_duplicates()
    report: dict[str, object] = {
        "fields": len(fields),
        "with_soil": int(fields["field_id"].isin(soil.dropna(subset=["nfk_mm"])["field_id"]).sum()),
        "soil_types": soil["soil_type"].value_counts().head(8).to_dict(),
    }
    print(json.dumps(report, ensure_ascii=False))
    data = data.merge(soil[["field_id", *SOIL_FEATURES]], on="field_id", how="left")
    split = {y: name for name, years in SPLITS.items() for y in years}
    for h in HORIZONS_DAYS:
        t = f"onset_{h}d"
        d = data.dropna(subset=[t]).assign(y=lambda x, t=t: x[t].astype(int))
        d = d.assign(split=d["year"].map(split))
        rows: dict[str, object] = {}
        for name, make in (("logistic", logistic_model), ("lightgbm", lightgbm_model)):
            res: dict[str, object] = {}
            for label, cols in (("no_soil", base), ("with_soil", base + SOIL_FEATURES)):
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
