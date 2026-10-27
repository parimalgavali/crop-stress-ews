"""Join extracted Sentinel-2, Sentinel-1 and weather tables onto the 5-day grid."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cropews.data.contract import validate_grid
from cropews.data.grid import build_grid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--district", default="Soest")
    parser.add_argument("--interim-dir", type=Path, default=Path("data/interim"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    tag = f"{args.district}_{args.year}"
    s2 = pd.read_parquet(args.interim_dir / "s2" / f"s2_{tag}.parquet")
    s1 = pd.read_parquet(args.interim_dir / "s1" / f"s1_{tag}.parquet")
    weather = pd.read_parquet(args.interim_dir / "weather" / f"weather_{tag}.parquet")
    field_ids = sorted(weather["field_id"].unique())
    missing = set(field_ids) - set(s2["field_id"]) - set(s1["field_id"])
    if missing:
        print(f"warning: {len(missing)} fields have no satellite rows")
    grid = validate_grid(build_grid(field_ids, args.year, s2, s1, weather))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"grid_{tag}.parquet"
    grid.to_parquet(out, index=False)
    rate = {c: f"{grid[c].mean():.0%}" for c in grid.columns if c.endswith("_observed")}
    print(f"wrote {out}: {len(grid)} rows; observed share per step {rate}")


if __name__ == "__main__":
    main()
