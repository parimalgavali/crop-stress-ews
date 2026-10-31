"""kNDVI stress-label test (second-round idea #5).

kNDVI = tanh(NDVI**2) (Camps-Valls et al. 2021) saturates less than NDVI at high
biomass, so peer-departure z-scores may flag stress more cleanly in dense wheat.
The test rebuilds events and onset targets with LABEL_INDICES = ("kndvi", "ndmi"),
retrains the served logistic model and compares AUROC with the current NDVI labels
on 2022 (validation, the ADR 0008 decision gate), 2024 and 2025.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from train_baselines import GRID_NAME

import cropews.labels as L
from cropews.baselines import logistic_model
from cropews.config import HORIZONS_DAYS, SPLITS
from cropews.features import build_features, feature_columns

DISTRICTS = ("Soest", "Warendorf", "Höxter", "Coesfeld", "Düren", "Rhein-Erft-Kreis")


def frames(processed: Path, interim: Path, indices: tuple[str, str]) -> pd.DataFrame:
    """Feature table whose onset targets come from labels built on ``indices``."""
    L.LABEL_INDICES = indices
    out = []
    for grid_path in sorted(processed.glob("grid_*.parquet")):
        district = GRID_NAME.fullmatch(grid_path.name)["district"]
        grid = pd.read_parquet(grid_path).assign(district=district)
        s2 = pd.concat(
            pd.read_parquet(f) for f in sorted((interim / "s2").glob(f"s2_{district}_*.parquet"))
        ).assign(district=district)
        if "kndvi" in indices:
            s2["kndvi"] = np.tanh(s2["ndvi"] ** 2)
        obs = L.clear_observations(s2)
        scored = L.score_peer(
            L.peer_residuals(obs), L.fit_peer_scale(L.peer_residuals(obs), SPLITS["train"])
        )
        events = L.find_events(scored)
        targets = L.make_targets(grid[["field_id", "year", "date"]], events, scored)
        feats = build_features(grid)
        out.append(feats.merge(targets, on=["field_id", "year", "date"]))
    return pd.concat(out, ignore_index=True)


def evaluate(data: pd.DataFrame, cols: list[str]) -> dict[str, dict[str, float]]:
    split = {y: name for name, years in SPLITS.items() for y in years}
    data = data.assign(split=data["year"].map(split))
    res: dict[str, dict[str, float]] = {}
    for h in HORIZONS_DAYS:
        d = data.dropna(subset=[f"onset_{h}d"]).assign(
            y=lambda x, t=f"onset_{h}d": x[t].astype(int)
        )
        model = logistic_model().fit(d[d.split == "train"][cols], d[d.split == "train"]["y"])
        res[f"{h}d"] = {
            name: round(
                float(
                    roc_auc_score(
                        d[d.split == name]["y"],
                        model.predict_proba(d[d.split == name][cols])[:, 1],
                    )
                ),
                3,
            )
            for name in ("validation", "test", "extra_check")
        }
    return res


def main() -> None:
    processed, interim = Path("data/processed"), Path("data/interim")
    base = frames(processed, interim, ("ndvi", "ndmi"))
    cols = [
        c
        for c in feature_columns(base.drop(columns=[c for c in base if c.startswith("onset_")]))
        if c != "in_event"
    ]
    report = {"ndvi": evaluate(base, cols)}
    kn = frames(processed, interim, ("kndvi", "ndmi"))
    report["kndvi"] = evaluate(kn, cols)
    report["target_rows"] = {
        "ndvi": int(base[[c for c in base if c.startswith("onset_")]].notna().sum().sum()),
        "kndvi": int(kn[[c for c in kn if c.startswith("onset_")]].notna().sum().sum()),
    }
    print(json.dumps(report, indent=2))
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/kndvi_label_eval.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
