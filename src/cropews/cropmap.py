"""In-season winter-wheat mapping from autumn/winter Sentinel-1/2 series (ADR 0018).

Features are monthly medians (October–March) per parcel, so a map is available by 1 April,
before the spring forecasts start and long before crop declarations are published.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cropews.config import NRW_WINTER_WHEAT_CROP_CODE
from cropews.labels import clear_observations

MONTHS = (10, 11, 12, 1, 2, 3)
S1_BANDS = ("vv_db", "vh_db", "vh_vv_db")
S2_BANDS = ("ndvi", "ndmi")
WINTER_CEREAL_CODES = frozenset({"115", "116", "131", "121", "156", "125"})


def _monthly(obs: pd.DataFrame, bands: tuple[str, ...], prefix: str) -> pd.DataFrame:
    month = pd.to_datetime(obs["date"]).dt.month
    obs = obs.assign(month=month)[
        obs.columns.intersection(["field_id", "year", *bands]).tolist() + ["month"]
    ]
    obs = obs[obs["month"].isin(MONTHS)]
    wide = obs.groupby(["field_id", "year", "month"])[list(bands)].median().unstack("month")
    wide.columns = [f"{prefix}{band}_m{m:02d}" for band, m in wide.columns]
    return wide


def features(s1: pd.DataFrame, s2: pd.DataFrame) -> pd.DataFrame:
    """One row per (field, season): monthly S1 and clear-S2 medians and their winter rise."""
    radar = _monthly(s1.dropna(subset=["vv_db"]), S1_BANDS, "s1_")
    optical = _monthly(clear_observations(s2), S2_BANDS, "s2_")
    out = radar.join(optical, how="outer")
    for band in S2_BANDS:
        early = out.filter(regex=rf"s2_{band}_m(10|11)$").mean(axis=1)
        late = out.filter(regex=rf"s2_{band}_m(02|03)$").mean(axis=1)
        out[f"s2_{band}_rise"] = late - early
    out["s1_vh_vv_rise"] = out.filter(regex=r"s1_vh_vv_db_m(02|03)$").mean(axis=1) - out.filter(
        regex=r"s1_vh_vv_db_m(10|11)$"
    ).mean(axis=1)
    return out.reset_index()


def targets(crops: pd.DataFrame) -> pd.DataFrame:
    """y_wheat: declared winter wheat; y_cereal: any winter cereal (incl. barley, rye)."""
    code = crops["crop_code"].astype(str)
    return crops.assign(
        y_wheat=(code == NRW_WINTER_WHEAT_CROP_CODE).astype(int),
        y_cereal=code.isin(WINTER_CEREAL_CODES).astype(int),
    )


def per_group_scores(frame: pd.DataFrame, prob: np.ndarray, target: str, by: str) -> pd.DataFrame:
    """Precision, recall and F1 at p >= 0.5 per group (e.g. district) and overall."""
    from sklearn.metrics import f1_score, precision_score, recall_score

    pred = (prob >= 0.5).astype(int)
    rows = []
    for name, idx in [*frame.groupby(by).indices.items(), ("all", np.arange(len(frame)))]:
        y, p = frame[target].to_numpy()[idx], pred[idx]
        rows.append(
            {
                by: name,
                "parcels": len(idx),
                "positives": int(y.sum()),
                "precision": precision_score(y, p, zero_division=0),
                "recall": recall_score(y, p, zero_division=0),
                "f1": f1_score(y, p, zero_division=0),
            }
        )
    return pd.DataFrame(rows)


def season_start(as_of: date) -> date:
    """1 October of the current winter season (harvest year = as_of.year or as_of.year + 1)."""
    return date(as_of.year if as_of.month >= 10 else as_of.year - 1, 10, 1)


def save_model(path: Path, model: Any, columns: list[str], threshold: float) -> None:
    import joblib

    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "columns": columns, "threshold": threshold}, path)


def predict(path: Path, s1: pd.DataFrame, s2: pd.DataFrame) -> dict[str, float]:
    """field_id -> probability of winter wheat; months not yet observed stay missing."""
    import joblib

    bundle = joblib.load(path)
    feats = features(s1, s2)
    x = feats.reindex(columns=bundle["columns"])
    prob = bundle["model"].predict_proba(x)[:, 1]
    return dict(zip(feats["field_id"], prob.astype(float), strict=True))
