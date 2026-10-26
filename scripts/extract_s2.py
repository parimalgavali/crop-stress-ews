"""Extract per-field Sentinel-2 series for a sample of winter-wheat fields in one district."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd

from cropews.config import EUROPE_LAND_MEMBER, PREDICTION_WINDOW
from cropews.data.contract import validate_observations
from cropews.data.fields import assign_districts, load_winter_wheat_fields, sample_fields
from cropews.data.sentinel2 import extract_field_series


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--district", default="Soest")
    parser.add_argument("--n", type=int, default=60)
    parser.add_argument("--min-size-ha", type=float, default=2.0)
    parser.add_argument("--iacs-dir", type=Path, default=Path("data/raw/iacs"))
    parser.add_argument("--districts", type=Path, required=True, help="BKG VG250/VG2500 KRS layer")
    parser.add_argument("--out-dir", type=Path, default=Path("data/interim/s2"))
    args = parser.parse_args()

    path = args.iacs_dir / EUROPE_LAND_MEMBER.format(year=args.year)
    fields = load_winter_wheat_fields(path, args.year, args.min_size_ha)
    fields = assign_districts(fields, gpd.read_file(args.districts))
    fields = sample_fields(fields[fields["district"] == args.district], args.n)
    start, end = (f"{args.year}-{d}" for d in PREDICTION_WINDOW)
    obs = validate_observations(extract_field_series(fields, start, end))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"s2_{args.district}_{args.year}.parquet"
    obs.to_parquet(out, index=False)
    clear = obs[obs["clear_fraction"] >= 0.8].groupby("field_id").size()
    print(f"wrote {out}: {len(obs)} rows; clear dates per field median {clear.median():.0f}")


if __name__ == "__main__":
    main()
