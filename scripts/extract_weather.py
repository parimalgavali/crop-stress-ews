"""Extract daily DWD weather (HYRAS + AMBAV 1 km grids) for winter-wheat fields in one district."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd

from cropews.config import EUROPE_LAND_MEMBER
from cropews.data.contract import validate_weather
from cropews.data.fields import assign_districts, load_winter_wheat_fields, sample_fields
from cropews.data.weather import extract_weather


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--district", default="Soest")
    parser.add_argument("--n", type=int, default=60)
    parser.add_argument("--min-size-ha", type=float, default=2.0)
    parser.add_argument("--iacs-dir", type=Path, default=Path("data/raw/iacs"))
    parser.add_argument("--districts", type=Path, required=True, help="BKG VG250/VG2500 KRS layer")
    parser.add_argument("--cache-dir", type=Path, default=Path("data/raw/dwd"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/interim/weather"))
    args = parser.parse_args()

    path = args.iacs_dir / EUROPE_LAND_MEMBER.format(year=args.year)
    fields = load_winter_wheat_fields(path, args.year, args.min_size_ha)
    fields = assign_districts(fields, gpd.read_file(args.districts))
    fields = sample_fields(fields[fields["district"] == args.district], args.n)
    if fields.empty:
        raise SystemExit(f"no winter-wheat fields >= {args.min_size_ha} ha in {args.district!r}")
    weather = validate_weather(extract_weather(fields, args.year, cache_dir=args.cache_dir))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"weather_{args.district}_{args.year}.parquet"
    weather.to_parquet(out, index=False)
    print(f"wrote {out}: {len(weather)} rows for {weather['field_id'].nunique()} fields")


if __name__ == "__main__":
    main()
