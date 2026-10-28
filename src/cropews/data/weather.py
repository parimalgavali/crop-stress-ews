"""Daily weather per field from DWD Climate Data Center 1 km grids (HYRAS and AMBAV)."""

from __future__ import annotations

import io
import os
import re
import shutil
import tarfile
import tempfile
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from cropews.data.contract import WEATHER_COLUMNS

CDC_DAILY = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily"
HYRAS_CRS = "EPSG:3035"
AMBAV_CRS = "EPSG:31467"  # Gauss-Krüger zone 3
HYRAS_VERSION = "v6-1"
# column -> (HYRAS variable, directory)
HYRAS = {
    "pr_mm": ("pr", "precipitation"),
    "tas_c": ("tas", "air_temperature_mean"),
    "tasmin_c": ("tasmin", "air_temperature_min"),
    "tasmax_c": ("tasmax", "air_temperature_max"),
    "hurs_pct": ("hurs", "humidity"),
}
# column -> (AMBAV product, scale to physical unit)
AMBAV = {
    "et0_mm": ("evapo_p", 0.1),
    "soil_moist_pct": ("soil_moist", 1.0),
}


def hyras_url(var: str, folder: str, year: int, version: str = HYRAS_VERSION) -> str:
    return f"{CDC_DAILY}/hyras_de/{folder}/{var}_hyras_1_{year}_{version}_de.nc"


def ambav_url(product: str, year: int, month: int) -> str:
    return f"{CDC_DAILY}/{product}/grids_germany_daily_{product}_{year}{month:02d}.tgz"


def fetch(url: str, cache_dir: Path) -> Path:
    """Download ``url`` into ``cache_dir`` once; later calls reuse the file."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / url.rsplit("/", 1)[-1]
    if not out.exists():
        # Unique temp file + atomic rename: concurrent fetches never share a partial file.
        fd, tmp = tempfile.mkstemp(dir=cache_dir, prefix=f".{out.name}.", suffix=".part")
        try:
            with os.fdopen(fd, "wb") as f, urllib.request.urlopen(url, timeout=300) as resp:
                shutil.copyfileobj(resp, f, 1 << 20)
            os.replace(tmp, out)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
    return out


def saturation_vapour_pressure(t_c: np.ndarray) -> np.ndarray:
    """FAO-56 eq. 11, kPa."""
    return 0.6108 * np.exp(17.27 * t_c / (t_c + 237.3))


def vapour_pressure_deficit(tmin: np.ndarray, tmax: np.ndarray, rh: np.ndarray) -> np.ndarray:
    """Daily VPD (kPa) from mean saturation vapour pressure (FAO-56 eq. 12) and mean RH."""
    es = (saturation_vapour_pressure(tmin) + saturation_vapour_pressure(tmax)) / 2
    return es * (1 - rh / 100)


def grid_index(transform: Any, shape: tuple[int, int], xs: np.ndarray, ys: np.ndarray):
    """Row/col of each point and a mask of points inside the grid."""
    from rasterio.transform import rowcol

    rows, cols = (np.asarray(a) for a in rowcol(transform, xs, ys))
    inside = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    return rows, cols, inside


def read_daily_stack(
    path: str, xs: np.ndarray, ys: np.ndarray, first_band: int, last_band: int
) -> np.ndarray:
    """Scaled values (days x points) from a one-band-per-day raster, reading only the points'
    window."""
    import rasterio
    from rasterio.windows import Window

    with rasterio.open(path) as src:
        rows, cols, inside = grid_index(src.transform, src.shape, xs, ys)
        out = np.full((last_band - first_band + 1, len(xs)), np.nan)
        if not inside.any():
            return out
        r0, r1 = rows[inside].min(), rows[inside].max()
        c0, c1 = cols[inside].min(), cols[inside].max()
        window = Window(c0, r0, c1 - c0 + 1, r1 - r0 + 1)
        bands = list(range(first_band, last_band + 1))
        data = src.read(bands, window=window).astype("float64")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        # NetCDF scale_factor/add_offset (e.g. HYRAS humidity is stored in 0.1 %).
        scales = np.array([src.scales[b - 1] for b in bands])[:, None, None]
        offsets = np.array([src.offsets[b - 1] for b in bands])[:, None, None]
        data = data * scales + offsets
        out[:, inside] = data[:, rows[inside] - r0, cols[inside] - c0]
    return out


def read_ascii_month(
    tgz: Path, xs: np.ndarray, ys: np.ndarray, scale: float
) -> dict[date, np.ndarray]:
    """Point values per day from a DWD monthly tar of daily ESRI ASCII grids."""
    from rasterio.io import MemoryFile

    out = {}
    with tarfile.open(tgz) as tar:
        for member in tar.getmembers():
            m = re.search(r"(\d{8})\.asc$", member.name)
            if not m:
                continue
            day = pd.Timestamp(m.group(1)).date()
            raw = tar.extractfile(member)
            assert raw is not None
            with MemoryFile(io.BytesIO(raw.read())) as mem, mem.open() as src:
                grid = src.read(1).astype("float64")
                grid[grid == src.nodata] = np.nan
                rows, cols, inside = grid_index(src.transform, src.shape, xs, ys)
            values = np.full(len(xs), np.nan)
            values[inside] = grid[rows[inside], cols[inside]] * scale
            out[day] = values
    return out


def _points(fields: gpd.GeoDataFrame, crs: str) -> tuple[np.ndarray, np.ndarray]:
    pts = gpd.GeoSeries(fields.geometry.representative_point(), crs=fields.crs).to_crs(crs)
    return pts.x.to_numpy(), pts.y.to_numpy()


def extract_weather(
    fields: gpd.GeoDataFrame,
    year: int,
    start: str = "01-01",
    end: str = "07-31",
    cache_dir: Path = Path("data/raw/dwd"),
    ambav: bool = True,
) -> pd.DataFrame:
    """One row per (field, day) with DWD 1 km weather at the field's representative point.

    ``ambav=False`` skips ET0 and soil moisture (left NaN): AMBAV is published monthly, so the
    current month is missing in live runs (ADR 0015).

    The window starts on 1 January by default so cumulative features (rain deficit, GDD)
    have a lead-in before predictions start on 1 April.
    """
    first, last = pd.Timestamp(f"{year}-{start}").date(), pd.Timestamp(f"{year}-{end}").date()
    days = [first + timedelta(d) for d in range((last - first).days + 1)]
    if fields.empty:
        return pd.DataFrame(columns=list(WEATHER_COLUMNS))
    n = len(fields)
    frame = pd.DataFrame(
        {
            "field_id": np.repeat(fields["field_id"].to_numpy(), len(days)),
            "year": year,
            "date": np.tile(np.array(days, dtype=object), n),
        }
    )

    xs, ys = _points(fields, HYRAS_CRS)
    b0, b1 = first.timetuple().tm_yday, last.timetuple().tm_yday
    for col, (var, folder) in HYRAS.items():
        path = fetch(hyras_url(var, folder, year), cache_dir / "hyras")
        frame[col] = read_daily_stack(f"netcdf:{path}:{var}", xs, ys, b0, b1).T.ravel()

    xs, ys = _points(fields, AMBAV_CRS)
    index = {d: i for i, d in enumerate(days)}
    for col, (product, scale) in AMBAV.items():
        values = np.full((len(days), n), np.nan)
        for month in range(first.month, last.month + 1) if ambav else []:
            tgz = fetch(ambav_url(product, year, month), cache_dir / product)
            for day, v in read_ascii_month(tgz, xs, ys, scale).items():
                if day in index:
                    values[index[day]] = v
        frame[col] = values.T.ravel()

    return add_vpd(frame)[list(WEATHER_COLUMNS)]


def add_vpd(frame: pd.DataFrame) -> pd.DataFrame:
    """Clip humidity to 100 % (float32 scaling gives e.g. 100.000001) and derive VPD."""
    frame["hurs_pct"] = frame["hurs_pct"].clip(upper=100.0)
    frame["vpd_kpa"] = vapour_pressure_deficit(
        frame["tasmin_c"].to_numpy(), frame["tasmax_c"].to_numpy(), frame["hurs_pct"].to_numpy()
    )
    return frame
