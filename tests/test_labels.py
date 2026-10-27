import numpy as np
import pandas as pd
import pytest

from cropews.labels import (
    clear_observations,
    find_events,
    fit_baseline,
    make_targets,
    score,
)


def _obs(year, ndvi, ndmi=0.3, field="a", dates=None, clear=1.0):
    dates = dates or pd.date_range(f"{year}-04-02", periods=len(ndvi), freq="10D")
    return pd.DataFrame(
        {
            "field_id": field,
            "year": year,
            "district": "Soest",
            "date": dates,
            "clear_fraction": clear,
            "ndvi": ndvi,
            "ndmi": ndmi,
        }
    )


def test_baseline_uses_training_years_only():
    train = pd.concat(_obs(2021, [0.5] * 3, field=f"f{i}") for i in range(25))
    test = pd.concat(_obs(2024, [0.1] * 3, field=f"g{i}") for i in range(25))
    base = fit_baseline(clear_observations(pd.concat([train, test])), train_years=[2021])
    assert (base["ndvi_mean"] == 0.5).all()
    with pytest.raises(ValueError):
        fit_baseline(clear_observations(test), train_years=[2021])


def test_baseline_drops_sparse_bins():
    base = fit_baseline(clear_observations(_obs(2021, [0.5, 0.6])), train_years=[2021])
    assert base.empty


def test_clear_observations_filters_cloudy_rows():
    obs = _obs(2024, [0.5, 0.6], clear=0.5)
    assert clear_observations(obs).empty


def _scored(below, year=2024, start="2024-04-02", step=5):
    dates = pd.date_range(start, periods=len(below), freq=f"{step}D")
    return pd.DataFrame({"field_id": "a", "year": year, "date": dates, "below": below})


def test_score_flags_ndvi_or_ndmi_anomaly():
    rng = np.random.default_rng(0)
    train = pd.concat(
        _obs(2021, rng.normal(0.6, 0.05, 3), rng.normal(0.3, 0.05, 3), field=f"f{i}")
        for i in range(30)
    )
    obs = clear_observations(pd.concat([train, _obs(2024, [0.6, 0.3, 0.6], [0.3, 0.3, 0.0])]))
    s = score(obs, fit_baseline(obs, [2021]))
    assert s[s["year"] == 2024]["below"].tolist() == [False, True, True]


def test_events_need_two_consecutive_below_dates():
    events = find_events(_scored([False, True, False, True, True, True, False]))
    assert len(events) == 1
    assert events["onset"][0] == pd.Timestamp("2024-04-17")
    assert events["recovery"][0] == pd.Timestamp("2024-05-02")


def test_events_after_senescence_cutoff_ignored_and_open_recovery():
    late = find_events(_scored([True, True], start="2024-07-05"))
    assert late.empty
    open_event = find_events(_scored([False, True, True]))
    assert pd.isna(open_event["recovery"][0])


def test_targets_horizons_exclusion_and_observability():
    scored = _scored([False, False, True, True, False, False, False, False, False, False])
    # clear dates: 2 Apr, 7, 12 (onset), 17, 22, 27 Apr, 2, 7, 12, 17 May
    events = find_events(scored)
    keys = pd.DataFrame(
        {
            "field_id": "a",
            "year": 2024,
            "date": pd.to_datetime(
                ["2024-04-01", "2024-04-06", "2024-04-13", "2024-05-17", "2024-06-25"]
            ),
        }
    )
    t = make_targets(keys, events, scored, horizons=(7, 14)).set_index("date")

    assert t.loc["2024-04-01", "onset_7d"] == 0  # onset 12 Apr is 11 days out
    assert t.loc["2024-04-01", "onset_14d"] == 1
    assert t.loc["2024-04-06", "onset_7d"] == 1
    assert t.loc["2024-04-13", "in_event"]  # onset 12 Apr <= t < recovery 22 Apr
    assert np.isnan(t.loc["2024-04-13", "onset_7d"])
    assert np.isnan(t.loc["2024-05-17", "onset_7d"])  # no clear date after 17 May
    assert np.isnan(t.loc["2024-06-25", "onset_14d"])  # t + h after senescence cutoff
