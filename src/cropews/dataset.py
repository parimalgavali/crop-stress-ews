"""Feature table: grid features joined with onset labels for every district-season on disk."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from cropews.config import SPLITS
from cropews.features import build_features

GRID_NAME = re.compile(r"grid_(?P<district>.+)_(?P<year>\d{4})\.parquet")


def load_feature_table(processed: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(processed.glob("grid_*.parquet")):
        m = GRID_NAME.fullmatch(path.name)
        labels = path.with_name(path.name.replace("grid_", "labels_"))
        if not m or not labels.exists():
            continue
        grid = pd.read_parquet(path).assign(district=m["district"])
        feats = build_features(grid)
        frames.append(feats.merge(pd.read_parquet(labels), on=["field_id", "year", "date"]))
    if not frames:
        raise SystemExit(f"no grid/label pairs in {processed}")
    data = pd.concat(frames, ignore_index=True)
    split = {y: name for name, years in SPLITS.items() for y in years}
    return data.assign(split=data["year"].map(split))
