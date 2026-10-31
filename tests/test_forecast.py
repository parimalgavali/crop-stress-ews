from datetime import date

import pandas as pd

from cropews.data.forecast import issued_features, observed_features
from cropews.live import forecast_summary


def test_issued_features_uses_the_run_from_the_issue_date() -> None:
    days = pd.date_range("2024-05-01", periods=10)
    archive = pd.concat(
        pd.DataFrame({"date": days, "lead": k, "pr_mm": float(k), "tasmin_c": -float(k)})
        for k in range(1, 6)
    )
    out = issued_features(archive).set_index("date")
    # issued 2024-05-01: lead 1 for 05-02 ... lead 5 for 05-06
    assert out.loc["2024-05-01", "fc_rain_5d"] == 15.0
    assert out.loc["2024-05-01", "fc_tmin_5d"] == -5.0
    assert out.index.max() == pd.Timestamp("2024-05-05")  # last issue with 5 leads


def test_observed_features_looks_only_forward() -> None:
    daily = pd.DataFrame(
        {
            "field_id": "a",
            "date": pd.date_range("2024-05-01", periods=8).astype(str),
            "pr_mm": [100.0, 1, 1, 1, 1, 1, 0, 0],
            "tasmin_c": [5.0, 4, 3, 2, 1, 0, 9, 9],
        }
    )
    out = observed_features(daily).set_index("date")
    assert out.loc["2024-05-01", "fc_rain_5d"] == 5.0  # excludes the 100 mm on the issue day
    assert out.loc["2024-05-01", "fc_tmin_5d"] == 0.0
    assert len(out) == 3


def test_forecast_summary_counts_frost_days() -> None:
    fc = pd.DataFrame(
        {
            "date": pd.date_range("2026-11-01", periods=7),
            "pr_mm": [9.0, 1, 2, 0, 0, 3, 50],
            "tasmin_c": [9.0, 2, -1, -3, 1, 4, 4],
        }
    )
    out = forecast_summary(fc, date(2026, 11, 1))
    assert out["fc_rain_5d_mm"] == 6.0
    assert out["fc_tmin_5d_c"] == -3.0
    assert out["fc_frost_days"] == 2
    assert out["fc_snow_5d_cm"] == 0.0  # column absent in archived data
    assert forecast_summary(fc, date(2026, 11, 5)) == {}


def test_forecast_summary_lists_days() -> None:
    fc = pd.DataFrame(
        {
            "date": pd.date_range("2026-11-01", periods=6),
            "pr_mm": [9.0, 1, 2, 0.04, 3, 50],
            "tasmin_c": [9.0, 2, -1, -3, 1, 4],
            "tasmax_c": [12.0, 6, 4, 2, 5, 8],
        }
    )
    out = forecast_summary(fc, date(2026, 11, 1))
    assert [x["date"] for x in out["fc_days"]] == [
        "2026-11-02",
        "2026-11-03",
        "2026-11-04",
        "2026-11-05",
        "2026-11-06",
    ]
    assert out["fc_days"][0] == {"date": "2026-11-02", "pr": 1.0, "tmin": 2.0, "tmax": 6.0}
    assert out["fc_days"][2]["pr"] == 0.0


def test_forecast_summary_sums_snow() -> None:
    fc = pd.DataFrame(
        {
            "date": pd.date_range("2026-11-01", periods=7),
            "pr_mm": [9.0, 1, 2, 0, 0, 3, 50],
            "tasmin_c": [9.0, 2, -1, -9, 1, 4, 4],
            "snow_cm": [0.0, 0, 0, 3, 1.5, 0, 10],
        }
    )
    out = forecast_summary(fc, date(2026, 11, 1))
    assert out["fc_snow_5d_cm"] == 4.5
