from __future__ import annotations

import pandas as pd


def test_scout_queue_ranks_by_declared_horizon_and_keeps_unavailable_visible() -> None:
    from cropews.scouting import scout_queue

    cards = {
        "a": {"district": "D", "horizons": [{"days": 14, "risk": 0.8, "level": "red"}]},
        "b": {"district": "D", "horizons": [{"days": 14, "risk": 0.8, "level": "red"}]},
        "c": {"district": "D", "horizons": [{"days": 7, "risk": 0.9, "level": "red"}]},
        "d": {"district": "D", "horizons": [{"days": 14, "risk": 0.1, "level": "green"}]},
    }
    quality = {"d": {"quality_status": "insufficient", "quality_reasons": ["no_optical"]}}
    out = scout_queue(cards, horizon=14, budget=2, quality=quality, checked_recently={"b"})
    # same risk -> field_id tie-break; "c" has no 14d entry; "d" moved to unavailable
    assert [e["field_id"] for e in out["queue"]] == ["a", "b"]
    assert out["queue"][1]["checked_recently"] is True
    assert out["n_ranked"] == 2
    assert out["unavailable"] == [
        {"field_id": "c", "reasons": ["no_forecast_at_horizon"]},
        {"field_id": "d", "reasons": ["no_optical"]},
    ]


def test_queue_capture_beats_random_on_correlated_scores() -> None:
    import numpy as np

    from cropews.scouting import queue_capture

    rng = np.random.default_rng(0)
    dates = pd.date_range("2024-05-01", periods=12).date
    fields = [f"f{i}" for i in range(40)]
    hot = set(fields[:8])  # these fields carry the events
    rows_s, rows_t = [], []
    for f in fields:
        base = 0.7 if f in hot else 0.2
        for d in dates:
            rows_s.append((f, d, base + rng.normal(0, 0.1)))
            rows_t.append((f, d, f in hot and rng.random() < 0.4))
    scores = pd.DataFrame(rows_s, columns=["field_id", "date", "risk"])
    targets = pd.DataFrame(rows_t, columns=["field_id", "date", "in_event"])
    out = queue_capture(scores, targets, horizon=14, k=10, random_draws=50)
    assert out["capture_model"] > out["capture_random"]
    assert out["dates"] > 0
