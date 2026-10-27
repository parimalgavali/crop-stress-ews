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


def test_lead_times_only_counts_alarms_before_onset() -> None:
    dates = pd.date_range("2024-04-05", periods=6, freq="5D")
    labels = pd.DataFrame(
        {
            "field_id": ["a"] * 6 + ["b"] * 6 + ["c"] * 6,
            "year": 2024,
            "date": list(dates) * 3,
            "in_event": [False, False, False, False, True, True]
            + [True] * 6
            + [False, False, False, True, True, True],
        }
    )
    preds = pd.DataFrame(
        {
            "field_id": ["a", "a", "b", "c"],
            "year": 2024,
            "date": [dates[1], dates[3], dates[0], dates[4]],
            "level": ["red", "red", "red", "red"],
        }
    )
    out = lead_times(labels, preds).set_index("field_id")
    assert "b" not in out.index
    assert out.loc["a", "lead_days"] == 15
    assert np.isnan(out.loc["c", "lead_days"])
