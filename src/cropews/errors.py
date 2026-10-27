"""Error analysis of the exported traffic lights: where alarms are wrong and how early they come."""

from __future__ import annotations

import numpy as np
import pandas as pd

AREA_BINS = (0.0, 2.0, 5.0, np.inf)
AREA_LABELS = ("<2 ha", "2–5 ha", "≥5 ha")
GAP_BINS = (-np.inf, 5.0, 15.0, np.inf)
GAP_LABELS = ("≤5 d", "6–15 d", ">15 d")


def add_strata(frame: pd.DataFrame) -> pd.DataFrame:
    """Field-size and Sentinel-2 cloud-gap bins (needs ``area_ha`` and ``s2_days_since``)."""
    gap = frame["s2_days_since"].fillna(np.inf)
    return frame.assign(
        size_bin=pd.cut(frame["area_ha"], AREA_BINS, labels=AREA_LABELS, right=False),
        cloud_gap=pd.cut(gap, GAP_BINS, labels=GAP_LABELS),
    )


def error_table(frame: pd.DataFrame, by: str, alarm_level: str = "red") -> pd.DataFrame:
    """Per-group alarm errors for rows with ``y`` (0/1), ``level``, ``field_id`` and ``year``."""

    def summarise(g: pd.DataFrame) -> pd.Series:
        alarm = (g["level"] == alarm_level).to_numpy()
        y = g["y"].to_numpy().astype(bool)
        fields = g[["field_id", "year"]].drop_duplicates().shape[0]
        return pd.Series(
            {
                "field_seasons": fields,
                "rows": len(g),
                "events": int(y.sum()),
                "misses": int((~alarm & y).sum()),
                "sensitivity": alarm[y].mean() if y.any() else np.nan,
                "false_alarms": int((alarm & ~y).sum()),
                "false_alarms_per_100_fields": 100 * (alarm & ~y).sum() / fields,
                "precision": y[alarm].mean() if alarm.any() else np.nan,
            }
        )

    return frame.groupby(by, observed=True)[["y", "level", "field_id", "year"]].apply(summarise)


def lead_times(labels: pd.DataFrame, preds: pd.DataFrame, alarm_level: str = "red") -> pd.DataFrame:
    """Days between the first alarm (any horizon) in the 21 days before onset and the onset.

    Onset is the first grid date a field is ``in_event``. Fields whose event starts on the first
    grid date are dropped (no history to warn from). ``lead_days`` is NaN when no alarm came.
    """
    first = labels[labels["in_event"]].groupby(["field_id", "year"])["date"].min()
    start = labels.groupby(["field_id", "year"])["date"].min()
    onset = first[first > start.reindex(first.index)].rename("onset").reset_index()
    alarms = preds[preds["level"] == alarm_level][["field_id", "year", "date"]].drop_duplicates()
    m = onset.merge(alarms, on=["field_id", "year"], how="left")
    before = (m["date"] < m["onset"]) & (m["date"] >= m["onset"] - pd.Timedelta(days=21))
    first_alarm = m[before].groupby(["field_id", "year"])["date"].min().rename("first_alarm")
    out = onset.merge(first_alarm.reset_index(), on=["field_id", "year"], how="left")
    return out.assign(lead_days=(out["onset"] - out["first_alarm"]).dt.days)
