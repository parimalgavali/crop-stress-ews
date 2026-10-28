"""Per-field Sentinel-1 RTC backscatter time series from Microsoft Planetary Computer."""

from __future__ import annotations

from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from cropews.data.contract import S1_OBSERVATION_COLUMNS
from cropews.data.sentinel2 import STAC_URL, aligned_window

COLLECTION = "sentinel-1-rtc"
NO_DATA = -32768.0

READ_ATTEMPTS = 3


def to_db(linear: float) -> float:
    return float(10 * np.log10(linear)) if linear > 0 else float("nan")


def valid_pixels(values: np.ndarray) -> np.ndarray:
    return np.isfinite(values) & (values > 0) & (values != NO_DATA)


def summarise_backscatter(vv: np.ndarray, vh: np.ndarray) -> dict[str, float]:
    """Coverage and median gamma0 (dB) over pixels valid in both polarisations.

    Medians are taken in linear power; the median commutes with the dB transform.
    """
    valid = valid_pixels(vv) & valid_pixels(vh)
    coverage = float(valid.mean()) if valid.size else 0.0
    if not valid.any():
        nan = float("nan")
        return {"coverage": coverage, "vv_db": nan, "vh_db": nan, "vh_vv_db": nan}
    vv_db = to_db(float(np.median(vv[valid])))
    vh_db = to_db(float(np.median(vh[valid])))
    return {"coverage": coverage, "vv_db": vv_db, "vh_db": vh_db, "vh_vv_db": vh_db - vv_db}


def select_backscatter(obs: pd.DataFrame, min_coverage: float = 0.9) -> pd.DataFrame:
    """Drop low-coverage rows; keep the best-covered slice per field, date and orbit."""
    obs = obs[obs["coverage"] >= min_coverage].sort_values("coverage")
    obs = obs.drop_duplicates(["field_id", "date", "orbit_state"], keep="last")
    return obs.sort_values(["field_id", "date", "orbit_state"]).reset_index(drop=True)


def extract_backscatter_series(
    fields: gpd.GeoDataFrame,
    start: str,
    end: str,
    inward_buffer_m: float = 10.0,
    min_coverage: float = 0.9,
    catalog: Any = None,
) -> pd.DataFrame:
    """One row per (field, acquisition date, orbit direction) with VV, VH and VH/VV in dB.

    Like the Sentinel-2 extractor, each acquisition is read once over the bounding box of all
    fields, so fields should be spatially clustered.
    """
    import planetary_computer
    import pystac_client
    import rasterio
    from rasterio.features import rasterize
    from rasterio.windows import from_bounds

    empty = pd.DataFrame(columns=list(S1_OBSERVATION_COLUMNS))
    if fields.empty:
        return empty
    if catalog is None:
        catalog = pystac_client.Client.open(STAC_URL)
    bbox = tuple(fields.to_crs(4326).total_bounds)
    items = catalog.search(collections=[COLLECTION], bbox=bbox, datetime=f"{start}/{end}").items()

    rows = []
    skipped: list[str] = []
    for item in sorted(items, key=lambda i: i.datetime):
        props = item.properties
        for attempt in range(READ_ATTEMPTS):
            try:
                with rasterio.open(planetary_computer.sign(item.assets["vv"].href)) as src:
                    local = fields.to_crs(src.crs)
                    local = local.assign(geometry=local.buffer(-inward_buffer_m))
                    local = local[~local.geometry.is_empty]
                    if local.empty:
                        return empty
                    window = from_bounds(*local.total_bounds, transform=src.transform)
                    window = window.round_offsets().round_lengths()
                    vv = src.read(1, window=window, boundless=True, fill_value=NO_DATA)
                    vv_transform = src.transform
                    transform = src.window_transform(window)
                with rasterio.open(planetary_computer.sign(item.assets["vh"].href)) as src:
                    vh = src.read(
                        1,
                        window=aligned_window(window, vv_transform, src.transform),
                        out_shape=vv.shape,
                        boundless=True,
                        fill_value=NO_DATA,
                    )
                break
            except rasterio.errors.RasterioIOError as err:
                print(f"S1 {item.id}: read failed ({attempt + 1}/{READ_ATTEMPTS}): {err}")
        else:
            skipped.append(item.id)
            continue  # skip a scene that cannot be read rather than fail the whole run
        for field_id, year, geom in zip(
            local["field_id"], local["year"], local.geometry, strict=False
        ):
            mask = rasterize([(geom, 1)], out_shape=vv.shape, transform=transform).astype(bool)
            if not mask.any():
                continue
            rows.append(
                {
                    "field_id": field_id,
                    "year": year,
                    "date": item.datetime.date(),
                    "orbit_state": props.get("sat:orbit_state"),
                    "relative_orbit": props.get("sat:relative_orbit"),
                    **summarise_backscatter(vv[mask], vh[mask]),
                }
            )
    out = select_backscatter(pd.DataFrame(rows), min_coverage) if rows else empty
    out.attrs["skipped_scenes"] = skipped  # read by live_update.py for run health
    return out
