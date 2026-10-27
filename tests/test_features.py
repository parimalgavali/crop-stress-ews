import numpy as np
import pandas as pd
import pytest

from cropews.features import build_features, feature_columns


def _grid(n=6, fields=("a",)):
    rows = []
    for f in fields:
        for i in range(n):
            rows.append(
                {
                    "field_id": f,
                    "year": 2024,
                    "district": "D",
                    "date": pd.Timestamp("2024-04-05") + pd.Timedelta(days=5 * i),
                    "ndvi": np.nan,
                    "ndmi": np.nan,
                    "ndre": np.nan,
                    "vh_db_asc": np.nan,
                    "vh_vv_db_asc": np.nan,
                    "vh_db_desc": np.nan,
                    "vh_vv_db_desc": np.nan,
                    "s2_days_since": 1.0,
                    "s1_asc_days_since": 1.0,
                    "s1_desc_days_since": 1.0,
                    "pr_mm": 5.0,
                    "et0_mm": 10.0,
                    "tas_c": 10.0,
                    "tasmax_c": 20.0,
                    "vpd_kpa": 0.5,
                    "soil_moist_pct": 80.0,
                    "weather_days": 5,
                }
            )
    return pd.DataFrame(rows)


def test_last_value_and_slope_carry_forward_only():
    g = _grid()
    g.loc[1, "ndvi"], g.loc[3, "ndvi"] = 0.8, 0.7
    f = build_features(g)
    assert np.isnan(f.loc[0, "ndvi_last"]) and f.loc[2, "ndvi_last"] == 0.8
    assert np.isnan(f.loc[2, "ndvi_slope"])
    assert f.loc[3, "ndvi_slope"] == pytest.approx(-0.1 / 10)
    assert f.loc[5, "ndvi_slope"] == pytest.approx(-0.1 / 10)


def test_features_do_not_see_the_future():
    g = _grid()
    g.loc[1, "ndvi"] = 0.8
    before = build_features(g)
    g.loc[4:, ["ndvi", "pr_mm", "tas_c", "tasmax_c"]] = [0.1, 100.0, 35.0, 40.0]
    after = build_features(g)
    cols = feature_columns(before)
    pd.testing.assert_frame_equal(before.loc[:3, cols], after.loc[:3, cols])


def test_peer_anomaly_against_district_median():
    g = _grid(n=2, fields=("a", "b", "c"))
    g.loc[g.field_id == "a", "ndvi"] = 0.5
    g.loc[g.field_id == "b", "ndvi"] = 0.8
    g.loc[g.field_id == "c", "ndvi"] = 0.9
    f = build_features(g)
    assert f.loc[f.field_id == "a", "ndvi_peer_anom"].iloc[0] == pytest.approx(-0.3)


def test_weather_windows_and_gdd():
    g = _grid(n=8)
    g.loc[7, "tasmax_c"] = 31.0
    f = build_features(g)
    assert f.loc[0, "water_balance_30d"] == -5
    assert f.loc[7, "water_balance_30d"] == -30  # six steps only
    assert f.loc[7, "hot_steps_30d"] == 1
    assert f.loc[3, "gdd"] == 4 * 50
