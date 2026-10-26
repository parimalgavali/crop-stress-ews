import numpy as np
import pandas as pd
import pytest

from cropews.data.sentinel1 import NO_DATA, select_backscatter, summarise_backscatter, to_db


def test_to_db():
    assert to_db(1.0) == 0.0
    assert to_db(0.01) == pytest.approx(-20.0)
    assert np.isnan(to_db(0.0))


def test_summarise_backscatter_medians_in_db_and_ratio():
    vv = np.array([0.1, 0.1, 0.1])
    vh = np.array([0.01, 0.01, 0.02])
    out = summarise_backscatter(vv, vh)
    assert out["coverage"] == 1.0
    assert out["vv_db"] == pytest.approx(-10.0)
    assert out["vh_db"] == pytest.approx(-20.0)
    assert out["vh_vv_db"] == pytest.approx(-10.0)


def test_summarise_backscatter_excludes_no_data_and_non_positive():
    vv = np.array([NO_DATA, 0.0, np.nan, 0.1])
    vh = np.array([0.01, 0.01, 0.01, 0.01])
    out = summarise_backscatter(vv, vh)
    assert out["coverage"] == pytest.approx(0.25)
    assert out["vv_db"] == pytest.approx(-10.0)


def test_summarise_backscatter_no_valid_pixels():
    out = summarise_backscatter(np.full(2, NO_DATA), np.full(2, NO_DATA))
    assert out["coverage"] == 0.0
    assert np.isnan(out["vv_db"]) and np.isnan(out["vh_vv_db"])


def test_select_backscatter_keeps_best_slice_per_orbit():
    obs = pd.DataFrame(
        {
            "field_id": ["a"] * 4,
            "date": ["2024-05-01"] * 3 + ["2024-05-03"],
            "orbit_state": ["ascending", "ascending", "descending", "ascending"],
            "coverage": [0.95, 1.0, 1.0, 0.4],
        }
    )
    out = select_backscatter(obs)
    assert out[["orbit_state", "coverage"]].values.tolist() == [
        ["ascending", 1.0],
        ["descending", 1.0],
    ]
