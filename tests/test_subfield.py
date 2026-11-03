import numpy as np

from cropews.subfield import anomaly_zones, downsample, mask_quality, zone_cells


def _field(h=20, w=20):
    scl = np.full((h, w), 4)
    interior = np.zeros((h, w), bool)
    interior[2:-2, 2:-2] = True
    ndvi = np.full((h, w), 0.6)
    return ndvi, scl, interior


def test_zones_find_contiguous_low_patch() -> None:
    ndvi, scl, interior = _field()
    ndvi[5:9, 5:9] = 0.2  # 4x4 patch well below the field median
    zones = anomaly_zones(ndvi, scl, interior)
    assert len(zones) == 1
    assert zones[0]["pixels"] == 16
    assert zones[0]["area_ha"] == 0.64
    assert zones[0]["mean_delta"] > 0.15


def test_zones_ignore_tiny_and_edge_patches() -> None:
    ndvi, scl, interior = _field()
    ndvi[5, 5] = 0.1  # below min_px
    ndvi[0, 0] = 0.1  # outside interior
    assert anomaly_zones(ndvi, scl, interior) == []


def test_zones_ignore_clouded_pixels() -> None:
    ndvi, scl, interior = _field()
    ndvi[5:9, 5:9] = 0.2
    scl[5:9, 5:9] = 8  # cloud
    assert anomaly_zones(ndvi, scl, interior) == []


def test_mask_quality_flags_unstable_view() -> None:
    ndvi, scl, interior = _field()
    scl[:, :10] = 3  # cloud shadow over half the view
    q = mask_quality(scl, interior)
    assert q["unstable"] is False or q["cloud_shadow"] > 0
    scl[:] = 8
    assert mask_quality(scl, interior)["unstable"] is True


def test_downsample_and_zone_cells() -> None:
    ndvi, _, interior = _field(56, 56)
    grid = downsample(ndvi, interior, max_size=28)
    assert grid.shape == (28, 28)
    cells = zone_cells({"row": 8, "col": 8, "height": 8, "width": 8}, (56, 56), (28, 28))
    assert (4, 4) in [tuple(c) for c in cells]
