import numpy as np
import pytest

from cropews.data.sentinel2 import clear_fraction, reflectance, spectral_indices, summarise_field


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
