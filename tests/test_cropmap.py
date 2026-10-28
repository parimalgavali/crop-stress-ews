from datetime import date

import numpy as np
import pandas as pd

from cropews.cropmap import cutoff_for, features, per_group_scores, season_start, targets


def _s1() -> pd.DataFrame:
    dates = pd.date_range("2023-10-05", "2024-03-25", freq="12D")
    rows = [
        {
            "field_id": f,
            "year": 2024,
            "date": d,
            "orbit_state": "ascending",
            "vv_db": -12.0 + i * 0.01,
            "vh_db": -18.0,
            "vh_vv_db": -6.0 + (f == "a") * 0.02 * i,
        }
        for f in ("a", "b")
        for i, d in enumerate(dates)
    ]
    return pd.DataFrame(rows)


def _s2() -> pd.DataFrame:
    dates = pd.to_datetime(["2023-10-20", "2023-11-15", "2024-02-20", "2024-03-10"])
    rows = [
        {
            "field_id": f,
            "year": 2024,
            "date": d,
            "clear_fraction": 1.0,
            "ndvi": 0.2 + (f == "a") * 0.15 * i,
            "ndmi": 0.0,
        }
        for f in ("a", "b")
        for i, d in enumerate(dates)
    ]
    return pd.DataFrame(rows)


def test_features_monthly_and_rise() -> None:
    f = features(_s1(), _s2()).set_index("field_id")
    assert {"s1_vv_db_m10", "s1_vv_db_m03", "s2_ndvi_m11", "s2_ndvi_rise"} <= set(f.columns)
    assert f.loc["a", "s2_ndvi_rise"] > 0.2
    assert abs(f.loc["b", "s2_ndvi_rise"]) < 1e-9
    assert f.loc["a", "s1_vh_vv_rise"] > f.loc["b", "s1_vh_vv_rise"]


def test_targets_and_scores() -> None:
    crops = targets(
        pd.DataFrame({"crop_code": ["115", "131", "411", 115], "district": list("xxyy")})
    )
    assert crops["y_wheat"].tolist() == [1, 0, 0, 1]
    assert crops["y_cereal"].tolist() == [1, 1, 0, 1]
    scores = per_group_scores(crops, np.array([0.9, 0.6, 0.1, 0.2]), "y_wheat", "district")
    overall = scores.set_index("district").loc["all"]
    assert overall["precision"] == 0.5 and overall["recall"] == 0.5


def test_season_start() -> None:
    assert season_start(date(2026, 11, 3)) == date(2026, 10, 1)
    assert season_start(date(2027, 3, 31)) == date(2026, 10, 1)


def test_cutoff_for() -> None:
    assert cutoff_for(date(2026, 11, 3)) is None
    assert cutoff_for(date(2026, 12, 5)) == "dec"
    assert cutoff_for(date(2027, 2, 10)) == "feb"
    assert cutoff_for(date(2027, 4, 5)) == "apr"
    assert cutoff_for(date(2027, 7, 1)) == "apr"
