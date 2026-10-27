import pandas as pd
import pytest

from cropews.sanity import event_rates, rate_yield_correlation


def test_event_rates_count_fields_once_and_fill_zero():
    fields = pd.DataFrame(
        {
            "district": ["A", "A", "A", "B"],
            "year": [2024, 2024, 2024, 2024],
            "field_id": ["f1", "f2", "f2", "g1"],
        }
    )
    events = pd.DataFrame({"field_id": ["f1", "f1"], "year": [2024, 2024], "onset": [1, 2]})
    r = event_rates(fields, events).set_index("district")
    assert r.loc["A", "fields"] == 2 and r.loc["A", "fields_with_event"] == 1
    assert r.loc["A", "share"] == pytest.approx(0.5)
    assert r.loc["B", "share"] == 0


def test_correlation_negative_when_events_track_yield_loss():
    table = pd.DataFrame(
        {"share": [0.1, 0.2, 0.3, 0.4, 0.5], "yield_anomaly": [0.1, 0.0, -0.1, -0.2, None]}
    )
    out = rate_yield_correlation(table)
    assert out["rho"] == pytest.approx(-1.0) and out["n"] == 4
