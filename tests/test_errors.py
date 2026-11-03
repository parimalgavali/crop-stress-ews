import numpy as np
import pandas as pd

from cropews.errors import add_strata, error_table, lead_times


def test_error_table_counts_misses_and_false_alarms() -> None:
    f = pd.DataFrame(
        {
            "field_id": ["a", "a", "b", "b"],
            "year": 2024,
            "district": ["X", "X", "Y", "Y"],
            "y": [1, 0, 1, 0],
            "level": ["red", "red", "green", "amber"],
        }
    )
    t = error_table(f, "district")
    assert t.loc["X", "misses"] == 0 and t.loc["X", "false_alarms"] == 1
    assert t.loc["X", "false_alarms_per_100_fields"] == 100
    assert t.loc["Y", "misses"] == 1 and t.loc["Y", "sensitivity"] == 0
    assert np.isnan(t.loc["Y", "precision"])


def test_strata_bins_and_missing_gap() -> None:
    f = add_strata(pd.DataFrame({"area_ha": [1.0, 2.0, 7.0], "s2_days_since": [3, 10, np.nan]}))
    assert list(f["size_bin"].astype(str)) == ["<2 ha", "2–5 ha", "≥5 ha"]
    assert list(f["cloud_gap"].astype(str)) == ["≤5 d", "6–15 d", ">15 d"]


def _labels() -> pd.DataFrame:
    dates = pd.date_range("2024-04-05", periods=8, freq="5D")
    return pd.DataFrame(
        {
            "field_id": ["a"] * 8 + ["b"] * 8 + ["c"] * 8,
            "year": 2024,
            "date": list(dates) * 3,
            "in_event": [False] * 4 + [True] * 4 + [True] * 8 + [False] * 5 + [True] * 3,
        }
    )


def test_lead_times_requires_the_alarm_horizon_to_reach_onset() -> None:
    # Review finding 4.2: a 7-day alarm 15 days before onset is not a valid warning.
    dates = pd.date_range("2024-04-05", periods=8, freq="5D")
    preds = pd.DataFrame(
        {
            "field_id": ["a", "a", "a", "c", "c"],
            "year": 2024,
            "date": [dates[0], dates[2], dates[4], dates[0], dates[6]],
            "horizon_days": [7, 14, 21, 7, 7],
            "level": ["red", "red", "red", "green", "red"],
        }
    )
    out = lead_times(_labels(), preds).set_index("field_id")
    assert "b" not in out.index  # already in event at the first predict date
    # a's onset = dates[4] (+20d). The dates[0] alarm covers only (+0,+7] -> too early.
    # The dates[2] (+10d) 14-day alarm covers (+10,+24] -> valid first warning.
    assert out.loc["a", "first_alarm"] == dates[2]
    assert out.loc["a", "lead_days"] == 10
    assert out.loc["a", "n_alarms"] == 1
    # the 21-day alarm at dates[4] is issued at onset, so it is not a warning
    # c's onset = dates[5] (+25d); its only alarm is a 7-day one at dates[6] -> after onset -> miss
    assert np.isnan(out.loc["c", "lead_days"])
    assert out.loc["c", "n_alarms"] == 0


def test_lead_times_uses_exact_event_onsets_and_reports_every_event() -> None:
    dates = pd.date_range("2024-04-05", periods=10, freq="5D")
    labels = pd.DataFrame(
        {
            "field_id": "a",
            "year": 2024,
            "date": dates,
            "in_event": [False] * 3 + [True] * 3 + [False] * 2 + [True] * 2,
        }
    )
    events = pd.DataFrame({"field_id": ["a", "a"], "year": 2024, "onset": [dates[3], dates[8]]})
    preds = pd.DataFrame(
        {
            "field_id": ["a", "a"],
            "year": 2024,
            "date": [dates[2], dates[6]],
            "horizon_days": [7, 14],
            "level": "red",
        }
    )
    out = lead_times(labels, preds, events=events).sort_values("onset").reset_index(drop=True)
    assert len(out) == 2  # both events reported, not just the first
    assert out.loc[0, "lead_days"] == 5  # dates[2] 7-day alarm covers onset dates[3]
    assert out.loc[1, "lead_days"] == 10  # dates[6] 14-day alarm covers onset dates[8]
