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

# Attribution wording used when the raw data does not support the physical claim (review 4.4):
# a positive contribution is an association, not evidence of the condition itself.
ATTRIB: dict[str, tuple[str, str]] = {
    "no_clear_image": (
        "Satellite coverage contributed to the estimate",
        "Satellitenabdeckung floss in die Schätzung ein",
    ),
    "behind_neighbours": (
        "Position versus neighbouring fields contributed to the estimate",
        "Abweichung von Nachbarfeldern floss in die Schätzung ein",
    ),
    "radar_change": (
        "Radar signal contributed to the estimate",
        "Radarsignal floss in die Schätzung ein",
    ),
    "greenness_dropping": (
        "Greenness trend contributed to the estimate",
        "Grünwert-Trend floss in die Schätzung ein",
    ),
    "dry_spell": (
        "Water balance contributed to the estimate",
        "Wasserbilanz floss in die Schätzung ein",
    ),
    "heat": ("Heat input contributed to the estimate", "Hitze floss in die Schätzung ein"),
    "dry_air": (
        "Air dryness contributed to the estimate",
        "Lufttrockenheit floss in die Schätzung ein",
    ),
    "dry_soil": (
        "Soil moisture contributed to the estimate",
        "Bodenfeuchte floss in die Schätzung ein",
    ),
    "crop_stage": (
        "Crop growth stage contributed to the estimate",
        "Wachstumsstadium floss in die Schätzung ein",
    ),
    "weak_canopy": (
        "Canopy level contributed to the estimate",
        "Bestandsniveau floss in die Schätzung ein",
    ),
}

# Groups whose physical claim must be verified against raw feature values before it is used.
# Each validator gets the raw feature row (x); NaN means unverifiable -> attribution.
STALE_DAYS = 15.0


def _factual(code: str, row: pd.Series) -> bool:
    """True when the raw feature values support the group's physical statement."""
    if code == "greenness_dropping":
        v = row.get("ndvi_slope")
        return bool(pd.notna(v) and v < 0)
    if code == "behind_neighbours":
        vals = [row[c] for c in row.index if c.endswith("_peer_anom") and pd.notna(row[c])]
        return bool(vals) and min(vals) < 0
    if code == "no_clear_image":
        for c in row.index:
            if c.startswith("missingindicator_") and row.get(c) == 1:
                return True
        vals = [row[c] for c in row.index if c.endswith("days_since") and pd.notna(row[c])]
        return bool(vals) and max(vals) > STALE_DAYS
    if code == "dry_spell":
        v = row.get("water_balance_30d")
        return bool(pd.notna(v) and v < 0)
    if code == "heat":
        v = row.get("hot_steps_30d")
        return bool(pd.notna(v) and v > 0)
    return False  # dry_air, dry_soil, crop_stage, weak_canopy, radar_change: not fact-checkable


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


def top_reasons(
    contrib: pd.DataFrame, x: pd.DataFrame | None = None, k: int = 2
) -> list[list[dict[str, str]]]:
    """Up to ``k`` groups pushing risk up, strongest first; empty list if none.

    With ``x`` (the raw feature rows behind ``contrib``), a group's physical text is only emitted
    when the data supports it; otherwise a neutral attribution text is used (``kind`` marks which).
    """
    out = []
    for i, row in contrib.iterrows():
        pos = row[row > 0].sort_values(ascending=False).head(k)
        items = []
        raw = x.loc[i] if x is not None and i in x.index else None
        for c in pos.index:
            fact = raw is not None and _factual(c, raw)
            en, de = TEXT[c] if fact else ATTRIB[c]
            items.append(
                {"code": c, "text_en": en, "text_de": de, "kind": "fact" if fact else "attribution"}
            )
        out.append(items)
    return out
