import numpy as np
import pandas as pd
import pytest

from cropews.baselines import logistic_model, persistence_score, weather_rule_score
from cropews.evaluation import bootstrap_ci, metrics, threshold_at_specificity


def _frame(n_fields=40, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for f in range(n_fields):
        for _ in range(10):
            y = int(rng.random() < 0.2)
            rows.append(
                {"field_id": f"f{f}", "year": 2024, "y": y, "score": y + rng.normal(0, 0.7)}
            )
    return pd.DataFrame(rows)


def test_threshold_gives_requested_specificity():
    fr = _frame()
    thr = threshold_at_specificity(fr["y"].to_numpy(), fr["score"].to_numpy())
    m = metrics(fr, thr)
    assert m["specificity"] == pytest.approx(0.9, abs=0.01)
    assert 0.5 < m["auroc"] <= 1 and "brier" not in m


def test_false_alarms_are_per_field_season():
    fr = pd.DataFrame(
        {"field_id": ["a", "a", "b", "b"], "year": 2024, "y": [0, 0, 0, 1], "score": [1, 1, 0, 1]}
    )
    m = metrics(fr, threshold=0.5)
    assert m["false_alarms_per_100_fields"] == 100  # 2 false alarms over 2 field-seasons
    assert m["brier"] == pytest.approx(0.5)


def test_bootstrap_ci_brackets_point_estimate():
    fr = _frame()
    point = metrics(fr, 0.5)["auroc"]
    lo, hi = bootstrap_ci(fr, lambda d: metrics(d, 0.5)["auroc"], n=200)
    assert lo < point < hi


def test_baselines_rank_risky_rows_higher():
    f = pd.DataFrame(
        {
            "ndvi_peer_anom": [0.0, -0.2],
            "ndmi_peer_anom": [0.0, np.nan],
            "water_balance_30d": [10.0, -40.0],
            "hot_steps_30d": [0.0, 1.0],
        }
    )
    assert persistence_score(f).is_monotonic_increasing
    assert weather_rule_score(f).is_monotonic_increasing


def test_logistic_model_handles_missing_values():
    rng = np.random.default_rng(0)
    x = pd.DataFrame({"a": rng.normal(size=200), "b": rng.normal(size=200)})
    y = (x["a"] > 0).astype(int)
    x.loc[::7, "a"] = np.nan
    proba = logistic_model().fit(x, y).predict_proba(x)[:, 1]
    assert ((proba > 0.5) == y)[x["a"].notna()].mean() > 0.9
