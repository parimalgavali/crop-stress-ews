import numpy as np
import pandas as pd
import pytest

from cropews.data.sentinel2 import (
    aligned_window,
    clear_fraction,
    reflectance,
    select_observations,
    spectral_indices,
    summarise_field,
)


def test_reflectance_applies_offset_from_baseline_04():
    dn = np.array([1000, 3000])
    assert reflectance(dn, "03.01").tolist() == pytest.approx([0.1, 0.3])
    assert reflectance(dn, "04.00").tolist() == pytest.approx([0.0, 0.2])
    assert reflectance(dn, "05.10").tolist() == pytest.approx([0.0, 0.2])


def test_spectral_indices_known_values():
    r = {
        b: np.array([v])
        for b, v in {"B02": 0.04, "B04": 0.05, "B05": 0.15, "B08": 0.45, "B11": 0.2}.items()
    }
    idx = spectral_indices(r)
    assert idx["ndvi"][0] == pytest.approx(0.4 / 0.5)
    assert idx["ndmi"][0] == pytest.approx(0.25 / 0.65)
    assert idx["ndre"][0] == pytest.approx(0.3 / 0.6)
    assert idx["msi"][0] == pytest.approx(0.2 / 0.45)
    assert idx["evi"][0] == pytest.approx(2.5 * 0.4 / (0.45 + 0.3 - 0.3 + 1))


def test_clear_fraction_ignores_no_data():
    assert clear_fraction(np.array([0, 0, 4, 5, 9, 8])) == pytest.approx(0.5)
    assert clear_fraction(np.array([0, 0])) == 0.0


def test_summarise_field_uses_clear_pixels_only():
    scl = np.array([4, 4, 9])
    refl = {
        "B02": np.array([0.04, 0.04, 0.5]),
        "B04": np.array([0.05, 0.05, 0.5]),
        "B05": np.array([0.15, 0.15, 0.5]),
        "B08": np.array([0.45, 0.45, 0.5]),
        "B11": np.array([0.2, 0.2, 0.5]),
    }
    out = summarise_field(scl, refl)
    assert out["clear_fraction"] == pytest.approx(2 / 3)
    assert out["ndvi"] == pytest.approx(0.8)


def test_summarise_field_all_cloudy_gives_nan():
    refl = {b: np.ones(2) for b in ("B02", "B04", "B05", "B08", "B11")}
    out = summarise_field(np.array([9, 8]), refl)
    assert out["clear_fraction"] == 0.0
    assert np.isnan(out["ndvi"])


def test_summarise_field_reports_scene_coverage():
    scl = np.array([0, 0, 4, 4])
    out = summarise_field(scl, {b: np.full(4, 0.3) for b in ("B02", "B04", "B05", "B08", "B11")})
    assert out["coverage"] == pytest.approx(0.5)
    assert out["clear_fraction"] == pytest.approx(1.0)


def test_select_observations_prefers_full_coverage_over_clear_sliver():
    obs = pd.DataFrame(
        {
            "field_id": ["a", "a", "a"],
            "date": ["2024-05-01"] * 2 + ["2024-05-06"],
            "coverage": [0.01, 1.0, 0.5],
            "clear_fraction": [1.0, 0.8, 1.0],
        }
    )
    out = select_observations(obs, min_coverage=0.9)
    assert out[["date", "coverage", "clear_fraction"]].values.tolist() == [["2024-05-01", 1.0, 0.8]]


def test_aligned_window_matches_ground_extent_on_finer_grid():
    from rasterio.transform import from_origin
    from rasterio.windows import Window, bounds

    scl_transform = from_origin(400000, 5700000, 20, 20)
    band_transform = from_origin(400000, 5700000, 10, 10)
    scl_window = Window(col_off=3, row_off=7, width=5, height=4)

    band_window = aligned_window(scl_window, scl_transform, band_transform)

    assert (band_window.col_off, band_window.row_off) == (6, 14)
    assert (band_window.width, band_window.height) == (10, 8)
    assert bounds(band_window, band_transform) == bounds(scl_window, scl_transform)
