"""Per-field Sentinel-2 L2A time series from Microsoft Planetary Computer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from cropews.data.contract import OBSERVATION_COLUMNS

# Scene classification: 4 = vegetation, 5 = bare soil.
CLEAR_SCL = (4, 5)
NO_DATA_SCL = 0
BANDS = ("B02", "B04", "B05", "B08", "B11")
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


def reflectance(dn: np.ndarray, processing_baseline: str) -> np.ndarray:
    """Convert L2A digital numbers to reflectance (baseline >= 04.00 adds a -1000 offset)."""
    offset = 1000.0 if processing_baseline >= "04.00" else 0.0
    return (dn.astype("float64") - offset) / 10000.0


def _nd(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return (a - b) / (a + b)


def spectral_indices(r: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    blue, red, red_edge, nir, swir = (r[b] for b in BANDS)
    with np.errstate(divide="ignore", invalid="ignore"):
        evi = 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)
        msi = swir / nir
    return {
        "ndvi": _nd(nir, red),
        "ndmi": _nd(nir, swir),
        "ndre": _nd(nir, red_edge),
        "evi": evi,
        "msi": msi,
    }


def clear_fraction(scl: np.ndarray) -> float:
    """Share of valid (non-no-data) pixels classed as vegetation or bare soil."""
    valid = scl[scl != NO_DATA_SCL]
    return float(np.isin(valid, CLEAR_SCL).mean()) if valid.size else 0.0


def summarise_field(scl: np.ndarray, refl: Mapping[str, np.ndarray]) -> dict[str, float]:
    """Median index values over clear pixels of one field on one date."""
    clear = np.isin(scl, CLEAR_SCL)
    coverage = float((scl != NO_DATA_SCL).mean()) if scl.size else 0.0
    out = {"coverage": coverage, "clear_fraction": clear_fraction(scl)}
    indices = spectral_indices({b: refl[b][clear] for b in BANDS})
    for name, values in indices.items():
        finite = values[np.isfinite(values)]
        out[name] = float(np.median(finite)) if finite.size else float("nan")
    return out


def select_observations(obs: pd.DataFrame, min_coverage: float = 0.9) -> pd.DataFrame:
    """Drop rows from scenes covering too little of the field; keep the clearest row per date."""
    obs = obs[obs["coverage"] >= min_coverage]
    obs = obs.sort_values(["clear_fraction", "coverage"])
    obs = obs.drop_duplicates(["field_id", "date"], keep="last")
    return obs.sort_values(["field_id", "date"]).reset_index(drop=True)


def aligned_window(window: Any, src_transform: Any, dst_transform: Any) -> Any:
    """Window on another grid covering exactly the ground extent of ``window``."""
    from rasterio.windows import bounds, from_bounds

    return from_bounds(*bounds(window, src_transform), transform=dst_transform)


def extract_field_series(
    fields: gpd.GeoDataFrame,
    start: str,
    end: str,
    max_cloud: float = 90.0,
    inward_buffer_m: float = 10.0,
    min_coverage: float = 0.9,
    catalog: Any = None,
) -> pd.DataFrame:
    """One row per (field, acquisition): clear fraction and median indices at 20 m.

    Fields should be spatially clustered (e.g. one district): each acquisition is read once
    over the bounding box of all fields.
    """
    import planetary_computer
    import pystac_client
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.features import rasterize
    from rasterio.windows import from_bounds

    empty = pd.DataFrame(columns=list(OBSERVATION_COLUMNS))
    if fields.empty:
        return empty
    if catalog is None:
        catalog = pystac_client.Client.open(STAC_URL)
    bbox = tuple(fields.to_crs(4326).total_bounds)
    items = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": max_cloud}},
    ).items()

    rows = []
    for item in sorted(items, key=lambda i: i.datetime):
        baseline = str(item.properties.get("s2:processing_baseline", "00.00"))
        with rasterio.open(planetary_computer.sign(item.assets["SCL"].href)) as src:
            local = fields.to_crs(src.crs)
            local = local.assign(geometry=local.buffer(-inward_buffer_m))
            local = local[~local.geometry.is_empty]
            if local.empty:
                return empty
            window = from_bounds(*local.total_bounds, transform=src.transform)
            window = window.round_offsets().round_lengths()
            scl = src.read(1, window=window, boundless=True, fill_value=NO_DATA_SCL)
            scl_transform = src.transform
            transform = src.window_transform(window)
        refl = {}
        for band in BANDS:
            with rasterio.open(planetary_computer.sign(item.assets[band].href)) as src:
                win = aligned_window(window, scl_transform, src.transform)
                dn = src.read(
                    1,
                    window=win,
                    out_shape=scl.shape,
                    boundless=True,
                    fill_value=0,
                    resampling=Resampling.average,
                )
            refl[band] = reflectance(dn, baseline)
        for field_id, year, geom in zip(
            local["field_id"], local["year"], local.geometry, strict=False
        ):
            mask = rasterize([(geom, 1)], out_shape=scl.shape, transform=transform).astype(bool)
            if not mask.any():
                continue
            summary = summarise_field(scl[mask], {b: refl[b][mask] for b in BANDS})
            rows.append(
                {"field_id": field_id, "year": year, "date": item.datetime.date(), **summary}
            )
    if not rows:
        return empty
    return select_observations(pd.DataFrame(rows), min_coverage)
