"""Fixed evaluation protocol: per-horizon discrimination, calibration and alarm burden."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

SPECIFICITY = 0.9


def threshold_at_specificity(y: np.ndarray, score: np.ndarray, spec: float = SPECIFICITY) -> float:
    """Score threshold whose specificity on (y, score) is ``spec``; fit it on validation data."""
    return float(np.quantile(score[y == 0], spec))


def metrics(frame: pd.DataFrame, threshold: float, score: str = "score") -> dict[str, float]:
    """Metrics for rows with columns ``y`` (0/1), ``score``, ``field_id`` and ``year``."""
    y, s = frame["y"].to_numpy(), frame[score].to_numpy()
    alarm = s > threshold
    field_seasons = frame[["field_id", "year"]].drop_duplicates().shape[0]
    out = {
        "auroc": roc_auc_score(y, s),
        "auprc": average_precision_score(y, s),
        "sensitivity": alarm[y == 1].mean(),
        "specificity": 1 - alarm[y == 0].mean(),
        "false_alarms_per_100_fields": 100 * (alarm & (y == 0)).sum() / field_seasons,
        "prevalence": y.mean(),
    }
    if s.min() >= 0 and s.max() <= 1:
        out["brier"] = brier_score_loss(y, s)
    return {k: float(v) for k, v in out.items()}


def bootstrap_ci(
    frame: pd.DataFrame,
    fn: Callable[[pd.DataFrame], float],
    n: int = 500,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Percentile CI resampling whole fields, since rows of one field are correlated."""
    rng = np.random.default_rng(seed)
    groups = {k: v.index.to_numpy() for k, v in frame.groupby("field_id")}
    keys = list(groups)
    stats = []
    for _ in range(n):
        idx = np.concatenate([groups[keys[i]] for i in rng.integers(0, len(keys), len(keys))])
        sample = frame.loc[idx]
        if sample["y"].nunique() == 2:
            stats.append(fn(sample))
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)
