"""Label sanity checks: event rates per district-season against official yield anomalies."""

from __future__ import annotations

import pandas as pd
from scipy.stats import spearmanr


def event_rates(fields: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Share of fields with at least one event per (district, year).

    ``fields`` has one row per (district, year, field_id) that was labelled; ``events`` has
    (field_id, year, onset). District-years without events get share 0.
    """
    fields = fields.drop_duplicates(["district", "year", "field_id"])
    hit = events[["field_id", "year"]].drop_duplicates().assign(has_event=True)
    merged = fields.merge(hit, on=["field_id", "year"], how="left")
    merged["has_event"] = merged["has_event"].notna()
    rates = merged.groupby(["district", "year"]).agg(
        fields=("field_id", "size"), fields_with_event=("has_event", "sum")
    )
    rates["share"] = rates["fields_with_event"] / rates["fields"]
    return rates.reset_index()


def rate_yield_correlation(table: pd.DataFrame) -> dict[str, float]:
    """Spearman correlation of ``share`` with ``yield_anomaly``; negative means the label tracks
    yield loss."""
    joined = table.dropna(subset=["share", "yield_anomaly"])
    rho, p = spearmanr(joined["share"], joined["yield_anomaly"])
    return {"rho": float(rho), "p": float(p), "n": float(len(joined))}


def within_season_correlation(table: pd.DataFrame) -> dict[str, float]:
    """Spearman of ``share`` vs ``yield_anomaly`` after removing each season's mean, i.e. do
    districts with more events than their peers in the same season lose more yield?"""
    joined = table.dropna(subset=["share", "yield_anomaly"])
    demeaned = joined[["share", "yield_anomaly"]] - joined.groupby("year")[
        ["share", "yield_anomaly"]
    ].transform("mean")
    rho, p = spearmanr(demeaned["share"], demeaned["yield_anomaly"])
    return {"rho": float(rho), "p": float(p), "n": float(len(joined))}
