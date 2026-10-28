"""Extract per-field Sentinel-1 backscatter series for a sample of winter-wheat fields."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd

from cropews.config import EUROPE_LAND_MEMBER, PREDICTION_WINDOW, WINTER_WINDOW
from cropews.data.contract import validate_s1_observations
from cropews.data.fields import assign_districts, load_winter_wheat_fields, sample_fields
from cropews.data.sentinel1 import extract_backscatter_series


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--district", default="Soest")
    parser.add_argument("--n", type=int, default=60)
    parser.add_argument("--min-size-ha", type=float, default=2.0)
    parser.add_argument("--iacs-dir", type=Path, default=Path("data/raw/iacs"))
    parser.add_argument("--districts", type=Path, required=True, help="BKG VG250/VG2500 KRS layer")
    parser.add_argument("--out-dir", type=Path, default=Path("data/interim/s1"))
    parser.add_argument(
        "--window",
        choices=("season", "winter"),
        default="season",
        help="season: Apr-Jul of --year; winter: Oct of --year - 1 to Mar of --year",
    )
    args = parser.parse_args()

    path = args.iacs_dir / EUROPE_LAND_MEMBER.format(year=args.year)
    fields = load_winter_wheat_fields(path, args.year, args.min_size_ha)
    fields = assign_districts(fields, gpd.read_file(args.districts))
    fields = sample_fields(fields[fields["district"] == args.district], args.n)
    if fields.empty:
        raise SystemExit(f"no winter-wheat fields >= {args.min_size_ha} ha in {args.district!r}")
    if args.window == "winter":
        start, end = f"{args.year - 1}-{WINTER_WINDOW[0]}", f"{args.year}-{WINTER_WINDOW[1]}"
    else:
        start, end = (f"{args.year}-{d}" for d in PREDICTION_WINDOW)
    obs = validate_s1_observations(extract_backscatter_series(fields, start, end))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_winter" if args.window == "winter" else ""
    out = args.out_dir / f"s1_{args.district}_{args.year}{suffix}.parquet"
    obs.to_parquet(out, index=False)
    per_field = obs.groupby("field_id")["date"].nunique()
    gaps = obs.drop_duplicates(["field_id", "date"]).sort_values("date").groupby("field_id")["date"]
    max_gap = gaps.apply(lambda d: d.diff().max().days if len(d) > 1 else float("nan"))
    print(
        f"wrote {out}: {len(obs)} rows; dates per field median "
        f"{per_field.median() if len(per_field) else 0:.0f}; "
        f"longest gap median {max_gap.median() if len(max_gap) else float('nan'):.0f} days"
    )


if __name__ == "__main__":
    main()
