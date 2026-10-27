import json

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from cropews.static_demo import build_season


def _inputs() -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    reasons = json.dumps([{"code": "dry_spell", "text_en": "x", "text_de": "y"}])
    preds = pd.DataFrame(
        {
            "field_id": ["a", "a", "a", "b"],
            "year": [2024, 2024, 2024, 2025],
            "date": pd.to_datetime(["2024-05-10", "2024-05-05", "2024-05-05", "2025-05-05"]),
            "horizon_days": [7, 14, 7, 7],
            "risk": [0.123456, 0.2, 0.3, 0.4],
            "level": ["green", "red", "amber", "green"],
            "reasons": [reasons, "[]", reasons, "[]"],
        }
    )
    fields = gpd.GeoDataFrame(
        {
            "field_id": ["a", "b", "c"],
            "year": [2024, 2025, 2024],
            "district": ["Soest"] * 3,
            "area_ha": [2.345, 3.0, 1.0],
        },
        geometry=[box(8.0, 51.5, 8.0123456789, 51.51), box(8, 51, 9, 52), box(7, 51, 8, 52)],
        crs="EPSG:4326",
    )
    return preds, fields


def test_build_season_shapes_and_orders() -> None:
    out = build_season(*_inputs(), year=2024)
    assert out["dates"] == ["2024-05-05", "2024-05-10"]
    assert [f["id"] for f in out["fields"]["features"]] == ["a"]  # c has no predictions
    assert out["risk"]["a"]["2024-05-05"] == [
        [7, 0.3, "amber", ["dry_spell"]],
        [14, 0.2, "red", []],
    ]
    assert out["risk"]["a"]["2024-05-10"] == [[7, 0.1235, "green", ["dry_spell"]]]
    props = out["fields"]["features"][0]["properties"]
    assert props == {"field_id": "a", "district": "Soest", "area_ha": 2.35}
    xs = [p[0] for p in out["fields"]["features"][0]["geometry"]["coordinates"][0]]
    assert 8.01235 in xs
    assert out["reasons"]["dry_spell"]["de"]
    json.dumps(out)
