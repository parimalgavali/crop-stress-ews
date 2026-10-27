"""Baselines every sequence model must beat (ADR 0008)."""

from __future__ import annotations

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler


def persistence_score(features: pd.DataFrame) -> pd.Series:
    """Current canopy anomaly continues: lower NDVI/NDMI than district peers -> higher risk."""
    anom = features[["ndvi_peer_anom", "ndmi_peer_anom"]].min(axis=1)
    return (-anom).fillna(0.0)


def weather_rule_score(features: pd.DataFrame) -> pd.Series:
    """Water deficit plus heat over the last 30 days, no satellite input."""
    return (-features["water_balance_30d"] + 10 * features["hot_steps_30d"]).fillna(0.0)


def logistic_model(seed: int = 0) -> Pipeline:
    return make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True),
        StandardScaler(),
        LogisticRegression(C=0.1, class_weight="balanced", max_iter=2000, random_state=seed),
    )


def lightgbm_model(seed: int = 0):  # type: ignore[no-untyped-def]
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=15,
        min_child_samples=20,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        class_weight="balanced",
        random_state=seed,
        verbose=-1,
    )
