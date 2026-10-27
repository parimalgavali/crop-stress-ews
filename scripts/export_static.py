"""Write ``web/public/demo/<year>.json`` for the static GitHub Pages demo (ADR 0014).

Input is the output of ``scripts/export_predictions.py``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from cropews.static_demo import build_season


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs-dir", type=Path, default=Path("data/outputs"))
    parser.add_argument("--out-dir", type=Path, default=Path("web/public/demo"))
    parser.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    args = parser.parse_args()

    preds = pd.read_parquet(args.outputs_dir / "predictions.parquet")
    fields = gpd.read_parquet(args.outputs_dir / "fields.geoparquet")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for year in args.years:
        payload = build_season(preds, fields, year)
        path = args.out_dir / f"{year}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        n = len(payload["fields"]["features"])
        print(f"wrote {path}: {n} fields, {len(payload['dates'])} dates, {path.stat().st_size} B")


if __name__ == "__main__":
    main()
