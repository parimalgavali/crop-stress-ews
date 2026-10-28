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


def test_extract_skips_a_scene_that_cannot_be_read(monkeypatch):
    from datetime import datetime
    from types import SimpleNamespace

    import geopandas as gpd
    import rasterio
    from shapely.geometry import box

    from cropews.data.sentinel1 import READ_ATTEMPTS, extract_backscatter_series

    calls = []

    def broken(*args, **kwargs):
        calls.append(args)
        raise rasterio.errors.RasterioIOError("Read failed")

    monkeypatch.setattr(rasterio, "open", broken)
    monkeypatch.setattr("planetary_computer.sign", lambda href: href)
    asset = SimpleNamespace(href="https://example.com/x.tif")
    item = SimpleNamespace(
        id="s1", datetime=datetime(2026, 10, 1), properties={}, assets={"vv": asset, "vh": asset}
    )
    catalog = SimpleNamespace(search=lambda **kw: SimpleNamespace(items=lambda: [item]))
    fields = gpd.GeoDataFrame(
        {"field_id": ["a"], "year": [2027]},
        geometry=[box(400000, 5700000, 400200, 5700200)],
        crs=25832,
    )
    out = extract_backscatter_series(fields, "2026-10-01", "2026-10-02", catalog=catalog)
    assert out.empty and len(calls) == READ_ATTEMPTS
