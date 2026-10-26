import numpy as np
import pandas as pd
import pytest

from cropews.data.contract import DataContractError, validate_grid
from cropews.data.grid import assign_step, build_grid, grid_dates


def test_grid_dates_cover_prediction_window_every_5_days():
    g = grid_dates(2024)
    assert g[0] == pd.Timestamp("2024-04-01")
    assert g[1] == pd.Timestamp("2024-04-06")
    assert g[-1] <= pd.Timestamp("2024-07-31")


def test_assign_step_uses_half_open_interval():
    g = grid_dates(2024)
    out = assign_step(pd.Series(["2024-03-27", "2024-03-28", "2024-04-01", "2024-04-02"]), g)
    assert out.isna().tolist() == [True, False, False, False]
    assert out[1] == out[2] == pd.Timestamp("2024-04-01")
    assert out[3] == pd.Timestamp("2024-04-06")


def _s2(dates, ndvi, clear=1.0):
    return pd.DataFrame(
        {
            "field_id": "a",
            "date": dates,
            "clear_fraction": clear,
            "ndvi": ndvi,
            **{c: 0.1 for c in ("ndmi", "ndre", "evi", "msi")},
        }
    )


def _s1(dates, orbit="ascending"):
    return pd.DataFrame(
        {
            "field_id": "a",
            "date": dates,
            "orbit_state": orbit,
            "vv_db": -10.0,
            "vh_db": -16.0,
            "vh_vv_db": -6.0,
        }
    )


def _weather(year=2024):
    days = pd.date_range(f"{year}-01-01", f"{year}-07-31")
    return pd.DataFrame(
        {
            "field_id": "a",
            "date": days,
            "pr_mm": 1.0,
            "tas_c": 10.0,
            "tasmin_c": 5.0,
            "tasmax_c": 15.0,
            "hurs_pct": 80.0,
            "vpd_kpa": 0.3,
            "et0_mm": 2.0,
            "soil_moist_pct": np.arange(len(days), dtype=float),
        }
    )


def test_build_grid_masks_missing_and_never_forward_fills():
    s2 = _s2(["2024-03-20", "2024-04-03", "2024-04-04", "2024-04-20"], [0.5, 0.6, 0.7, np.nan])
    s2.loc[3, "clear_fraction"] = 0.2
    grid = validate_grid(build_grid(["a"], 2024, s2, _s1(["2024-04-05"]), _weather()))
    rows = grid.set_index("date")

    first, second, third = (
        rows.loc[pd.Timestamp(d)] for d in ("2024-04-01", "2024-04-06", "2024-04-11")
    )
    assert not first["s2_observed"] and np.isnan(first["ndvi"])
    assert first["s2_days_since"] == 12  # 20 March, before the window, still counts
    assert second["s2_observed"] and second["ndvi"] == 0.7  # latest clear in the step
    assert second["s2_days_since"] == 2
    assert not third["s2_observed"] and np.isnan(third["ndvi"])
    assert third["s2_days_since"] == 7
    assert second["s1_asc_observed"] and second["vv_db_asc"] == -10.0
    assert not second["s1_desc_observed"] and np.isnan(second["s1_desc_days_since"])


def test_build_grid_aggregates_weather_over_step():
    grid = build_grid(["a"], 2024, _s2([], []), _s1([]), _weather())
    first = grid.iloc[0]
    assert first["pr_mm"] == 5.0 and first["et0_mm"] == 10.0
    assert first["weather_days"] == 5 and first["weather_observed"]
    assert first["soil_moist_pct"] == pd.Timestamp("2024-04-01").dayofyear - 1  # last day


def test_validate_grid_rejects_inconsistent_mask():
    grid = build_grid(["a"], 2024, _s2(["2024-04-03"], [0.6]), _s1([]), _weather())
    grid.loc[2, "s2_observed"] = True  # 11 April: last clear 8 days earlier
    with pytest.raises(DataContractError, match="days_since"):
        validate_grid(grid)
