"""Pooled vs per-district calibration of the Live risk model (open question, project memory).

The served model is Platt-scaled and thresholded on the pooled 2022 validation season;
Coesfeld shows many false alarms. Test: within 2022, 5-fold over fields — fit Platt and
red/amber thresholds either pooled or per district on the calibration folds, evaluate
out-of-fold on the held fold. Adopt per-district only if it cuts false alarms (Coesfeld)
without losing sensitivity at red.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from train_baselines import load

from cropews.baselines import logistic_model
from cropews.config import HORIZONS_DAYS, SPLITS
from cropews.evaluation import threshold_at_specificity
from cropews.features import feature_columns

FOLDS = 5
SPEC_RED, SPEC_AMBER = 0.90, 0.75


def platt(z: np.ndarray, y: np.ndarray) -> LogisticRegression:
    return LogisticRegression().fit(z.reshape(-1, 1), y)


def calibrate(cal: pd.DataFrame, held: pd.DataFrame, ycol: str) -> pd.DataFrame:
    """Pooled calibration: Platt + thresholds on all calibration rows."""
    zc = cal["z"].to_numpy().reshape(-1, 1)
    p = platt(zc, cal[ycol].astype(int).to_numpy())
    risk_cal = p.predict_proba(zc)[:, 1]
    risk = p.predict_proba(held["z"].to_numpy().reshape(-1, 1))[:, 1]
    return held.assign(
        risk=risk,
        red=risk > threshold_at_specificity(cal[ycol].astype(int).to_numpy(), risk_cal, SPEC_RED),
        amber=risk
        > threshold_at_specificity(cal[ycol].astype(int).to_numpy(), risk_cal, SPEC_AMBER),
    )


def calibrate_by_district(cal: pd.DataFrame, held: pd.DataFrame, ycol: str) -> pd.DataFrame:
    """Per-district calibration; districts with a one-class calibration set fall back to pooled."""
    pooled = calibrate(cal, held, ycol)[["field_id", "date", "risk", "red", "amber"]]
    out = []
    for dist, h in held.groupby("district"):
        c = cal[cal["district"] == dist]
        if c[ycol].nunique() < 2 or len(c) < 50:
            fb = pooled[pooled["field_id"].isin(h["field_id"])]
            out.append(h.merge(fb, on=["field_id", "date"], how="left"))
            continue
        out.append(calibrate(c, h, ycol))
    return pd.concat(out)


def summarize(frame: pd.DataFrame, fields: int) -> dict[str, float]:
    y = frame["y"].astype(int).to_numpy()
    red = frame["red"].to_numpy()
    return {
        "sensitivity_red": float(red[y == 1].mean()) if y.sum() else float("nan"),
        "false_alarms_per_100_fields": float(100 * (red & (y == 0)).sum() / fields),
        "amber_or_red_share": float((frame["red"] | frame["amber"]).mean()),
    }


def main() -> None:
    data = load(Path("data/processed"))
    cols = feature_columns(data.drop(columns=[c for c in data if c.startswith("onset_")]))
    cols = [c for c in cols if c != "in_event"]
    split = {y: name for name, years in SPLITS.items() for y in years}
    data["split"] = data["year"].map(split)
    val = data[data["split"] == "validation"]
    fields = sorted(val["field_id"].unique())
    rng = np.random.default_rng(0)
    rng.shuffle(fields)
    folds = [set(f) for f in np.array_split(fields, FOLDS)]

    report: dict[str, object] = {"val_fields": len(fields), "horizons": {}}
    for h in HORIZONS_DAYS:
        t = f"onset_{h}d"
        d = data.dropna(subset=[t]).assign(y=lambda x, t=t: x[t].astype(int))
        model = logistic_model().fit(
            d[d.split == "train"][cols], d[d.split == "train"]["y"].astype(int)
        )
        vd = d[d.split == "validation"].assign(
            z=model.decision_function(d[d.split == "validation"][cols])
        )
        pooled_all, dist_all = [], []
        for fold in folds:
            held = vd[vd["field_id"].isin(fold)]
            cal = vd[~vd["field_id"].isin(fold)]
            pooled_all.append(calibrate(cal, held, "y"))
            dist_all.append(calibrate_by_district(cal, held, "y"))
        res: dict[str, object] = {}
        for name, frames in (("pooled", pooled_all), ("per_district", dist_all)):
            oof = pd.concat(frames)
            res[name] = {
                "all": summarize(oof, len(fields)),
                "by_district": {
                    dist: summarize(g, g["field_id"].nunique())
                    for dist, g in oof.groupby("district")
                },
            }
        report["horizons"][h] = res
        print(f"--- {h}d ---")
        for name in res:
            print(name, json.dumps(res[name]["all"], indent=1))
            for dist, m in res[name]["by_district"].items():
                print(
                    f"  {dist:<18} sens {m['sensitivity_red']:.2f} "
                    f"FA/100 {m['false_alarms_per_100_fields']:.0f}"
                )
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/district_calibration.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
