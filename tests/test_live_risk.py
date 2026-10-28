from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from cropews.baselines import logistic_model
from cropews.data.grid import build_grid
from cropews.features import build_features, feature_columns
from cropews.live_risk import score_live, spring_active

IDS = ["a", "b"]


def _sources() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    days = pd.date_range("2027-03-01", "2027-07-31")
    s2 = pd.DataFrame(
        [
            {
                "field_id": f,
                "date": d,
                "clear_fraction": 1.0,
                "ndvi": 0.5 + 0.1 * i,
                "ndmi": 0.1,
                "ndre": 0.1,
                "evi": 0.1,
                "msi": 1.0,
            }
            for i, f in enumerate(IDS)
            for d in pd.date_range("2027-04-02", "2027-06-30", freq="7D")
        ]
    )
    s1 = pd.DataFrame(
        [
            {
                "field_id": f,
                "date": d,
                "orbit_state": "ascending",
                "vv_db": -10.0,
                "vh_db": -16.0,
                "vh_vv_db": -6.0,
            }
            for f in IDS
            for d in pd.date_range("2027-04-03", "2027-06-30", freq="6D")
        ]
    )
    w = pd.DataFrame(
        [
            {
                "field_id": f,
                "date": d,
                "pr_mm": 1.0,
                "tas_c": 10.0,
                "tasmin_c": 5.0,
                "tasmax_c": 15.0,
                "hurs_pct": 80.0,
                "vpd_kpa": 0.3,
                "et0_mm": np.nan,
                "soil_moist_pct": np.nan,
            }
            for f in IDS
            for d in days
        ]
    )
    return s2, s1, w


def _bundle(s2, s1, w) -> dict:
    g = build_grid(IDS, 2027, s2, s1, w).assign(district="X")
    f = build_features(g)
    cols = [c for c in feature_columns(f) if c not in ("water_balance_30d", "soil_moist_pct")]
    y = (np.arange(len(f)) % 2).astype(int)
    model = logistic_model().fit(f[cols], y)
    platt = LogisticRegression().fit(model.decision_function(f[cols]).reshape(-1, 1), y)
    hz = {"model": model, "platt": platt, "amber": 0.4, "red": 0.6}
    return {"columns": cols, "horizons": {7: hz, 14: hz, 21: hz}}


def test_spring_active_window() -> None:
    assert not spring_active(date(2027, 4, 4))
    assert spring_active(date(2027, 4, 5)) and spring_active(date(2027, 6, 23))
    assert not spring_active(date(2027, 6, 24))
    assert not spring_active(date(2026, 11, 1))


def test_score_live_uses_only_data_up_to_as_of() -> None:
    s2, s1, w = _sources()
    bundle = _bundle(s2, s1, w)
    districts = pd.Series("X", index=IDS)
    as_of = date(2027, 5, 1)
    cards, rows = score_live(bundle, districts, s2, s1, w, as_of)
    assert set(cards) == set(IDS)
    assert all(c["date"] <= as_of.isoformat() for c in cards.values())
    assert [h["days"] for h in cards["a"]["horizons"]] == [7, 14, 21]
    assert len(rows) == 6 and {r["level"] for r in rows} <= {"green", "amber", "red"}
    # later data must not change a forecast already issued
    cut = [d[d["date"] <= pd.Timestamp(as_of)] for d in (s2, s1, w)]
    again, _ = score_live(bundle, districts, *cut, as_of)
    assert again["a"]["horizons"][0]["risk"] == cards["a"]["horizons"][0]["risk"]


def test_score_live_drops_horizons_past_senescence() -> None:
    s2, s1, w = _sources()
    cards, rows = score_live(
        _bundle(s2, s1, w), pd.Series("X", index=IDS), s2, s1, w, date(2027, 6, 20)
    )
    last = max(pd.Timestamp(c["date"]) for c in cards.values())
    expect = [h for h in (7, 14, 21) if last + pd.Timedelta(days=h) <= pd.Timestamp("2027-06-30")]
    assert expect and expect != [7, 14, 21]
    assert all([h["days"] for h in c["horizons"]] == expect for c in cards.values())
    assert {r["horizon_days"] for r in rows} == set(expect)
