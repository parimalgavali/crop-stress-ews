import io
import tarfile

import numpy as np
import pytest
from rasterio.transform import from_origin

from cropews.data.weather import (
    ambav_url,
    grid_index,
    hyras_url,
    read_ascii_month,
    read_daily_stack,
    saturation_vapour_pressure,
    vapour_pressure_deficit,
)


def test_urls():
    assert hyras_url("pr", "precipitation", 2024).endswith(
        "hyras_de/precipitation/pr_hyras_1_2024_v6-1_de.nc"
    )
    assert ambav_url("evapo_p", 2024, 5).endswith("evapo_p/grids_germany_daily_evapo_p_202405.tgz")


def test_saturation_vapour_pressure_fao56_table():
    assert saturation_vapour_pressure(np.array(20.0)) == pytest.approx(2.338, abs=1e-3)


def test_vpd_zero_at_saturation_and_positive_when_dry():
    t = np.array([10.0, 10.0])
    assert vapour_pressure_deficit(t, t + 10, np.array([100.0, 50.0])).tolist() == pytest.approx(
        [0.0, 0.5 * (saturation_vapour_pressure(10.0) + saturation_vapour_pressure(20.0)) / 2]
    )


def test_grid_index_flags_points_outside():
    transform = from_origin(0, 3000, 1000, 1000)
    rows, cols, inside = grid_index(
        transform, (3, 3), np.array([500, 2500, 5000]), np.array([2500, 500, 500])
    )
    assert rows[:2].tolist() == [0, 2] and cols[:2].tolist() == [0, 2]
    assert inside.tolist() == [True, True, False]


def test_read_daily_stack_reads_points_and_masks_nodata(tmp_path):
    import rasterio

    data = np.arange(4 * 3 * 3, dtype="float32").reshape(4, 3, 3)
    data[2, 1, 1] = -999
    path = tmp_path / "stack.tif"
    profile = dict(
        driver="GTiff",
        count=4,
        height=3,
        width=3,
        dtype="float32",
        nodata=-999,
        transform=from_origin(0, 3000, 1000, 1000),
        crs="EPSG:3035",
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data)

    out = read_daily_stack(
        str(path), np.array([1500.0, 2500.0, 9e9]), np.array([1500.0, 500.0, 0.0]), 2, 3
    )

    assert out.shape == (2, 3)
    assert out[:, 0][0] == data[1, 1, 1] and np.isnan(out[1, 0])
    assert out[:, 1].tolist() == [data[1, 2, 2], data[2, 2, 2]]
    assert np.isnan(out[:, 2]).all()


def test_read_ascii_month_scales_and_parses_dates(tmp_path):
    grid = "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1000\nNODATA_value -9999\n"
    grid += "10 20\n-9999 40\n"
    tgz = tmp_path / "grids_germany_daily_evapo_p_202405.tgz"
    with tarfile.open(tgz, "w:gz") as tar:
        payload = grid.encode()
        info = tarfile.TarInfo("grids_germany_daily_evapo_p_20240501.asc")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))

    out = read_ascii_month(tgz, np.array([1500.0, 500.0]), np.array([1500.0, 500.0]), 0.1)

    ((day, values),) = out.items()
    assert str(day) == "2024-05-01"
    assert values[0] == pytest.approx(2.0)
    assert np.isnan(values[1])


def test_read_daily_stack_applies_scale_factor(tmp_path):
    import rasterio

    path = tmp_path / "hurs.tif"
    profile = dict(
        driver="GTiff",
        count=1,
        height=1,
        width=1,
        dtype="int16",
        nodata=-999,
        transform=from_origin(0, 1000, 1000, 1000),
        crs="EPSG:3035",
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.array([[[775]]], dtype="int16"))
        dst.scales = (0.1,)

    out = read_daily_stack(str(path), np.array([500.0]), np.array([500.0]), 1, 1)

    assert out[0, 0] == pytest.approx(77.5)
