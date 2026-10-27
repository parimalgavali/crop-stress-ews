"""Traffic-light levels and plain-language reasons for a risk score (ADR 0012).

Reasons come from the calibrated logistic model's per-feature contributions
(coefficient × standardised value), summed into a few farmer-readable groups.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

# (substring in feature name, code, English, German); first match wins.
REASON_GROUPS: tuple[tuple[str, str, str, str], ...] = (
    (
        "missingindicator",
        "no_clear_image",
        "No clear satellite image recently",
        "Kein klares Satellitenbild in letzter Zeit",
    ),
    (
        "days_since",
        "no_clear_image",
        "No clear satellite image recently",
        "Kein klares Satellitenbild in letzter Zeit",
    ),
    (
        "peer_anom",
        "behind_neighbours",
        "Crop is behind neighbouring fields",
        "Bestand liegt hinter den Nachbarfeldern",
    ),
    (
        "vh_",
        "radar_change",
        "Radar shows a change in the crop",
        "Radar zeigt eine Veränderung im Bestand",
    ),
    (
        "vv_",
        "radar_change",
        "Radar shows a change in the crop",
        "Radar zeigt eine Veränderung im Bestand",
    ),
    ("_slope", "greenness_dropping", "Crop greenness is dropping", "Grünwert des Bestands sinkt"),
    (
        "water_balance",
        "dry_spell",
        "Little rain in the last 30 days",
        "Wenig Regen in den letzten 30 Tagen",
    ),
    ("hot_steps", "heat", "Hot days recently", "Kürzlich heiße Tage"),
    ("vpd", "dry_air", "Very dry air", "Sehr trockene Luft"),
    ("soil_moist", "dry_soil", "Soil is drying out", "Boden trocknet aus"),
    ("gdd", "crop_stage", "Crop growth stage", "Wachstumsstadium"),
    ("doy", "crop_stage", "Crop growth stage", "Wachstumsstadium"),
    ("", "weak_canopy", "Crop canopy is weak", "Bestand ist schwach"),
)
TEXT = {code: (en, de) for _, code, en, de in REASON_GROUPS}


def reason_code(feature: str) -> str:
    return next(code for key, code, _, _ in REASON_GROUPS if key in feature)


def level(risk: np.ndarray, amber: float, red: float) -> np.ndarray:
    return np.where(risk >= red, "red", np.where(risk >= amber, "amber", "green"))


def contributions(model: Pipeline, x: pd.DataFrame) -> pd.DataFrame:
    """Per-row logit contribution of each reason group for an imputer→scaler→logistic pipeline."""
    pre, clf = model[:-1], model[-1]
    z = pre.transform(x) * clf.coef_[0]
    names = [
        n.replace("missingindicator_", "missingindicator ") for n in pre.get_feature_names_out()
    ]
    per_feature = pd.DataFrame(z, columns=names, index=x.index)
    return per_feature.T.groupby([reason_code(n) for n in names]).sum().T


def top_reasons(contrib: pd.DataFrame, k: int = 2) -> list[list[dict[str, str]]]:
    """Up to ``k`` groups pushing risk up, strongest first; empty list if none."""
    out = []
    for _, row in contrib.iterrows():
        pos = row[row > 0].sort_values(ascending=False).head(k)
        out.append([{"code": c, "text_en": TEXT[c][0], "text_de": TEXT[c][1]} for c in pos.index])
    return out
