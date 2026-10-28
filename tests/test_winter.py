import numpy as np
import pandas as pd

from cropews.winter import emergence_scores, spring_outcome, summarise, winter_observations


def _s2(years=(2020, 2021), n=25, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for y in years:
        dates = pd.date_range(f"{y - 1}-10-05", f"{y}-03-30", freq="10D")
        for f in range(n):
            for d in dates:
                ndvi = 0.6 + rng.normal(0, 0.03) - (0.3 if f == 0 else 0)
                rows.append((f"f{f}", y, "Soest", d, 1.0, ndvi, 0.2 + rng.normal(0, 0.02)))
    cols = ["field_id", "year", "district", "date", "clear_fraction", "ndvi", "ndmi"]
    return pd.DataFrame(rows, columns=cols)


def test_winter_window_skips_october():
    obs = winter_observations(_s2())
    assert not (obs["date"].dt.month == 10).any()
    assert (obs["date"].dt.month == 3).any()


def test_weak_field_is_flagged_and_predicts_event():
    s2 = _s2()
    scores = emergence_scores(s2, train_years=[2020])
    flagged = scores[scores["weak_emergence"]]
    assert set(flagged["field_id"]) == {"f0"}
    events = pd.DataFrame({"field_id": ["f0", "f3"], "year": [2021, 2021]})
    out = spring_outcome(scores[scores["year"] == 2021], events)
    s = summarise(out)
    assert s["flagged"] == 1 and s["event_rate_flagged"] == 1.0
    assert s["auroc"] > 0.5


def test_wet_date_needs_drop_and_rain():
    from cropews.winter import wet_dates, wet_summary

    dates = pd.date_range("2023-11-01", periods=20, freq="3D")
    vv = [-10.0] * 20
    vv[10] = -14.0  # drop after rain
    vv[15] = -14.0  # drop without rain
    s1 = pd.DataFrame(
        {"field_id": "a", "year": 2024, "date": dates, "orbit_state": "ascending", "vv_db": vv}
    )
    days = pd.date_range("2023-10-20", "2024-01-31")
    pr = [0.0] * len(days)
    for d in pd.date_range(dates[10] - pd.Timedelta(days=4), dates[10]):
        pr[days.get_loc(d)] = 6.0
    daily = pd.DataFrame({"field_id": "a", "date": days, "pr_mm": pr})
    daily = pd.concat([daily.iloc[:50], daily.iloc[50:].reset_index(drop=True)])
    w = wet_dates(s1, daily)
    assert w["wet"].sum() == 1 and bool(w.loc[10, "wet"])
    s = wet_summary(w)
    assert s.loc[0, "n_wet"] == 1 and s.loc[0, "n_radar"] == 20
