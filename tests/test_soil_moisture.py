import pandas as pd
import pytest

from cropews.data.forecast import soil_moisture_features


def test_change_is_mean_of_next_five_days_minus_today():
    daily = pd.DataFrame(
        {
            "date": pd.date_range("2025-05-01", periods=8),
            "sm_top": 0.3,
            "sm_root": [0.30, 0.29, 0.28, 0.27, 0.26, 0.25, 0.24, 0.23],
        }
    )
    f = soil_moisture_features(daily)
    assert f["sm_root_change_5d"].iloc[0] == pytest.approx(0.27 - 0.30)
    assert f["sm_root_change_5d"].iloc[2] == pytest.approx(0.25 - 0.28)
    assert f["sm_root_change_5d"].iloc[3:].isna().all()
