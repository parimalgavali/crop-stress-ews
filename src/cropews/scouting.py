"""Budgeted scouting queue (spec 8.2): which fields to inspect first, and how good the order is.

Two queues: a risk queue (fields ranked by a declared horizon's risk, stable tie-break) and a
quality queue (eligible fields that cannot be ranked — kept visible, never silently green).
``queue_capture`` evaluates top-k event capture against persistence and random ranking on held
seasons.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def scout_queue(
    cards: dict[str, dict[str, Any]],
    horizon: int,
    budget: int,
    quality: dict[str, dict[str, Any]] | None = None,
    checked_recently: set[str] | None = None,
) -> dict[str, Any]:
    """Rank scored fields by ``horizon`` risk (desc, then field_id) up to ``budget``.

    ``quality``: field_id -> evidence record (status/reasons shown on entries); fields whose
    evidence is ``insufficient`` are moved to ``unavailable`` — visible, not green.
    ``checked_recently``: field_ids a scout already visited (marked, still ranked).
    """
    quality = quality or {}
    checked_recently = checked_recently or set()
    entries, unavailable = [], []
    for fid, card in cards.items():
        h = next((x for x in card.get("horizons", []) if x["days"] == horizon), None)
        q = quality.get(fid, {})
        if q.get("quality_status") == "insufficient":
            unavailable.append({"field_id": fid, "reasons": q.get("quality_reasons", [])})
        elif h is None:
            unavailable.append({"field_id": fid, "reasons": ["no_forecast_at_horizon"]})
        else:
            entries.append(
                {
                    "field_id": fid,
                    "district": card.get("district"),
                    "risk": h["risk"],
                    "level": h["level"],
                    "quality_status": q.get("quality_status"),
                    "checked_recently": fid in checked_recently,
                }
            )
    # fields whose evidence is insufficient but that carry no card at all stay visible too
    for fid, q in quality.items():
        if fid not in cards and q.get("quality_status") == "insufficient":
            unavailable.append({"field_id": fid, "reasons": q.get("quality_reasons", [])})
    entries.sort(key=lambda e: (-e["risk"], e["field_id"]))
    for rank, e in enumerate(entries[:budget], start=1):
        e["rank"] = rank
    return {
        "horizon_days": horizon,
        "budget": budget,
        "queue": entries[:budget],
        "n_ranked": len(entries),
        "unavailable": sorted(unavailable, key=lambda u: u["field_id"]),
    }


def queue_capture(
    scores: pd.DataFrame,
    targets: pd.DataFrame,
    horizon: int,
    k: int,
    seed: int = 0,
    random_draws: int = 200,
) -> dict[str, Any]:
    """Share of in-event target rows caught by a top-k queue per date.

    ``scores``: field_id, date, risk (one horizon). ``targets``: field_id, date, in_event.
    Baselines: persistence (rank by the previous date's score per field) and random order
    (mean over ``random_draws`` seeded shuffles).
    """
    rng = np.random.default_rng(seed)
    pos = targets[targets["in_event"]].set_index(["field_id", "date"]).index
    by_date = {d: g["field_id"].tolist() for d, g in targets.groupby("date") if len(g)}
    prev = scores.sort_values("date").groupby("field_id")["risk"].shift(1)
    prev.index = pd.MultiIndex.from_frame(scores[["field_id", "date"]])
    cap: dict[str, list[float]] = {"model": [], "persistence": [], "random": []}
    for d, fids in by_date.items():
        n_pos = sum((f, d) in pos for f in fids)
        if n_pos == 0:
            continue
        s = scores[scores["date"] == d].set_index("field_id")["risk"]
        model_top = set(s.sort_values(ascending=False).head(k).index)
        p = prev.xs(d, level="date").dropna()
        persist_top = set(p.sort_values(ascending=False).head(k).index)
        pool = list(s.index)
        rand = np.mean(
            [
                sum((f, d) in pos for f in rng.choice(pool, size=min(k, len(pool)), replace=False))
                / n_pos
                for _ in range(random_draws)
            ]
        )
        cap["model"].append(sum((f, d) in pos for f in model_top) / n_pos)
        cap["persistence"].append(sum((f, d) in pos for f in persist_top) / n_pos)
        cap["random"].append(float(rand))
    return {
        "horizon_days": horizon,
        "k": k,
        "dates": len(cap["model"]),
        "capture_model": round(float(np.mean(cap["model"])), 4) if cap["model"] else None,
        "capture_persistence": (
            round(float(np.mean(cap["persistence"])), 4) if cap["persistence"] else None
        ),
        "capture_random": round(float(np.mean(cap["random"])), 4) if cap["random"] else None,
    }
