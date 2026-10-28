"""Yearly champion/challenger retraining of the Live spring risk model (US-28, ADR 0026).

A challenger is fitted with the ``export_live_model`` recipe on more seasons. Both models are then
scored on a holdout season that neither has seen, and the challenger replaces the champion only
if it is better on average and not clearly worse at any horizon.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from cropews.baselines import logistic_model
from cropews.config import HORIZONS_DAYS
from cropews.evaluation import threshold_at_specificity

# A horizon may lose at most this much AUROC for the challenger to be promoted.
MAX_HORIZON_DROP = 0.01


def fit_bundle(train: pd.DataFrame, val: pd.DataFrame, cols: list[str]) -> dict[str, Any]:
    """Logistic model per horizon, Platt-scaled on ``val``, red/amber at 90 %/75 % specificity."""
    bundle: dict[str, Any] = {"columns": cols, "horizons": {}}
    for h in HORIZONS_DAYS:
        target = f"onset_{h}d"
        tr, va = train.dropna(subset=[target]), val.dropna(subset=[target])
        model = logistic_model().fit(tr[cols], tr[target].astype(int))
        z = model.decision_function(va[cols]).reshape(-1, 1)
        y = va[target].astype(int).to_numpy()
        platt = LogisticRegression().fit(z, y)
        risk = platt.predict_proba(z)[:, 1]
        bundle["horizons"][h] = {
            "model": model,
            "platt": platt,
            "red": threshold_at_specificity(y, risk, 0.90),
            "amber": threshold_at_specificity(y, risk, 0.75),
        }
    return bundle


def holdout_auroc(bundle: dict[str, Any], holdout: pd.DataFrame) -> dict[int, float]:
    out = {}
    for h, b in sorted(bundle["horizons"].items()):
        d = holdout.dropna(subset=[f"onset_{h}d"])
        score = b["model"].decision_function(d[bundle["columns"]])
        out[int(h)] = round(float(roc_auc_score(d[f"onset_{h}d"].astype(int), score)), 3)
    return out


def decide(champion: dict[int, float], challenger: dict[int, float]) -> dict[str, Any]:
    delta = {h: round(challenger[h] - champion[h], 3) for h in champion}
    mean = round(sum(delta.values()) / len(delta), 3)
    promote = mean > 0 and min(delta.values()) >= -MAX_HORIZON_DROP
    return {"delta": delta, "mean_delta": mean, "promote": promote}
