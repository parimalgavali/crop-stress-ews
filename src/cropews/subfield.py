"""Subfield anomaly zones from a per-pixel index map (spec 8.6, ADR 0070).

A field's freshest clear Sentinel-2 view is kept as a small pixel map. Pixels well
below the field's own clear-pixel median form contiguous candidate zones; mask
quality (cloud/shadow, edge/exterior pixels, unstable view) is reported alongside.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

CLEAR_SCL = (4, 5)
NO_DATA_SCL = 0

# A patch counts when it is at least this far below the field's clear-interior median.
ZONE_DELTA = 0.15
MIN_ZONE_PX = 4
MIN_INSIDE_PX = 10
UNSTABLE_CLEAR = 0.5
MAX_GRID = 28


def mask_quality(scl: np.ndarray, interior: np.ndarray) -> dict:
    """Shares of clear / cloud-shadow pixels inside the usable field interior."""
    inside = scl[interior]
    valid = inside != NO_DATA_SCL
    if not valid.any():
        return {"clear": 0.0, "cloud_shadow": 1.0, "unstable": True, "interior_px": 0}
    clear = np.isin(inside, CLEAR_SCL)
    clear_share = float(clear[valid].mean())
    return {
        "clear": clear_share,
        "cloud_shadow": round(float((~clear)[valid].mean()), 3),
        "unstable": clear_share < UNSTABLE_CLEAR,
        "interior_px": int(interior.sum()),
    }


def anomaly_zones(
    ndvi: np.ndarray,
    scl: np.ndarray,
    interior: np.ndarray,
    delta: float = ZONE_DELTA,
    min_px: int = MIN_ZONE_PX,
    pixel_m: float = 20.0,
) -> list[dict]:
    """Contiguous clear-interior pixels below field median − delta → candidate zones."""
    inside = interior & np.isin(scl, CLEAR_SCL) & np.isfinite(ndvi)
    if inside.sum() < MIN_INSIDE_PX:
        return []
    median = float(np.median(ndvi[inside]))
    anomalous = inside & (ndvi < median - delta)
    labels, n = ndimage.label(anomalous, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    px_area_ha = (pixel_m * pixel_m) / 10_000.0
    out = []
    for i in range(1, n + 1):
        rows, cols = np.where(labels == i)
        if rows.size < min_px:
            continue
        out.append(
            {
                "row": int(rows.min()),
                "col": int(cols.min()),
                "height": int(rows.max() - rows.min() + 1),
                "width": int(cols.max() - cols.min() + 1),
                "pixels": int(rows.size),
                "area_ha": round(rows.size * px_area_ha, 2),
                "mean_delta": round(float(median - ndvi[labels == i].mean()), 3),
            }
        )
    return sorted(out, key=lambda z: -z["pixels"])


def downsample(ndvi: np.ndarray, valid: np.ndarray, max_size: int = MAX_GRID) -> np.ndarray:
    """Block-mean NDVI to at most max_size cells per side; invalid cells → NaN."""
    h, w = ndvi.shape
    step_r = max(1, -(-h // max_size))
    step_c = max(1, -(-w // max_size))
    out_h, out_w = -(-h // step_r), -(-w // step_c)
    out = np.full((out_h, out_w), np.nan)
    for r in range(out_h):
        for c in range(out_w):
            cell = ndvi[r * step_r : (r + 1) * step_r, c * step_c : (c + 1) * step_c]
            ok = valid[r * step_r : (r + 1) * step_r, c * step_c : (c + 1) * step_c]
            vals = cell[ok & np.isfinite(cell)]
            if vals.size:
                out[r, c] = np.median(vals)
    return out


def zone_cells(
    zone: dict, ndvi_shape: tuple[int, int], grid_shape: tuple[int, int]
) -> list[list[int]]:
    """Map a zone's bounding box from pixel coords onto the downsampled grid."""
    h, w = ndvi_shape
    gh, gw = grid_shape
    r0 = int(zone["row"] * gh / h)
    r1 = int((zone["row"] + zone["height"] - 1) * gh / h)
    c0 = int(zone["col"] * gw / w)
    c1 = int((zone["col"] + zone["width"] - 1) * gw / w)
    return [[r, c] for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def field_subfield(
    geom: object,
    crs: object,
    item: object,
    catalog_item_reader: object = None,
) -> dict | None:
    """Build the payload entry for one field's freshest view (spec 8.6)."""
    from cropews.data.sentinel2 import field_index_map

    m = field_index_map(geom, crs, item)
    if m is None:
        return None
    quality = mask_quality(m["scl"], m["interior"])
    zn = anomaly_zones(m["ndvi"], m["scl"], m["interior"])
    valid = m["interior"] & (m["scl"] != NO_DATA_SCL)
    grid = downsample(m["ndvi"], valid)
    entry = {
        "date": str(item.datetime.date()),
        "quality": quality,
        "zones": zn,
        "grid": {
            "h": int(grid.shape[0]),
            "w": int(grid.shape[1]),
            "ndvi": [[round(float(v), 2) if np.isfinite(v) else None for v in row] for row in grid],
            "zone_cells": sorted(
                {tuple(c) for z in zn for c in zone_cells(z, m["ndvi"].shape, grid.shape)}
            ),
        },
    }
    return entry
