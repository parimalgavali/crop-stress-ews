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


def _events_from_labels(labels: pd.DataFrame) -> pd.DataFrame:
    """Onsets = first date of each contiguous ``in_event`` run (fallback when no events table)."""
    g = labels.sort_values(["field_id", "year", "date"])
    run = g["in_event"] & ~g.groupby(["field_id", "year"])["in_event"].shift(fill_value=False)
    return g[run][["field_id", "year", "date"]].rename(columns={"date": "onset"})


def lead_times(
    labels: pd.DataFrame,
    preds: pd.DataFrame,
    events: pd.DataFrame | None = None,
    alarm_level: str = "red",
) -> pd.DataFrame:
    """Valid-warning analysis per event (review finding 4.2).

    An alarm (``level == alarm_level`` issued at ``date`` with ``horizon_days``) only counts for an
    event when its own interval contains the onset: ``date < onset <= date + horizon_days``. Events
    come from the exact ``events`` table (field_id, year, onset) when given, else from contiguous
    ``in_event`` runs in ``labels``; every event is reported, not just the first per field-season.
    Events starting on or before the first predict date are dropped (nothing could warn them).

    Columns: ``onset``, ``first_alarm`` (earliest matching forecast origin), ``lead_days`` (NaN when
    no valid alarm — a missed event) and ``n_alarms`` (matching forecasts = repeated-alert burden).
    One forecast may warn several events; each event counts it against its own onset.
    """
    if events is None:
        events = _events_from_labels(labels)
    else:
        events = events[["field_id", "year", "onset"]].copy()
    first_pred = preds.groupby(["field_id", "year"])["date"].min()
    keep = events.merge(first_pred.rename("first_pred").reset_index(), on=["field_id", "year"])
    keep = keep[keep["onset"] > keep["first_pred"]][["field_id", "year", "onset"]]
    alarms = preds[preds["level"] == alarm_level][
        ["field_id", "year", "date", "horizon_days"]
    ].drop_duplicates()
    m = keep.merge(alarms, on=["field_id", "year"], how="left")
    hit = (
        m["date"].notna()
        & (m["date"] < m["onset"])
        & (m["onset"] <= m["date"] + pd.to_timedelta(m["horizon_days"], unit="D"))
    )
    valid = (
        m[hit]
        .groupby(["field_id", "year", "onset"])["date"]
        .agg(first_alarm="min", n_alarms="size")
    )
    out = keep.merge(valid.reset_index(), on=["field_id", "year", "onset"], how="left")
    out["n_alarms"] = out["n_alarms"].fillna(0).astype(int)
    return out.assign(lead_days=(out["onset"] - out["first_alarm"]).dt.days)
