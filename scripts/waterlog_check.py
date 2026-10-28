"""Winter waterlogging check on a past season (ADR 0016): radar drops after heavy rain.

Reads data/interim/s1w/s1_<district>_<year>_winter.parquet, pulls DWD HYRAS rain for the same
fields from 1 October of the year before, and relates wet radar dates to spring stress events.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cropews.config import CORE_DISTRICTS, EUROPE_LAND_MEMBER, WINTER_WINDOW
from cropews.data.fields import load_winter_wheat_fields
from cropews.data.weather import extract_weather
from cropews.winter import wet_dates, wet_summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--iacs-dir", type=Path, default=Path("data/raw/iacs"))
    parser.add_argument("--s1w-dir", type=Path, default=Path("data/interim/s1w"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--cache-dir", type=Path, default=Path("data/raw/dwd"))
    args = parser.parse_args()

    path = args.iacs_dir / EUROPE_LAND_MEMBER.format(year=args.year)
    fields = load_winter_wheat_fields(path, args.year)
    rows = []
    for district in CORE_DISTRICTS:
        s1_path = args.s1w_dir / f"s1_{district}_{args.year}_winter.parquet"
        if not s1_path.exists():
            continue
        s1 = pd.read_parquet(s1_path)
        sample = fields[fields["field_id"].isin(s1["field_id"].unique())]
        daily = pd.concat(
            [
                extract_weather(sample, args.year - 1, WINTER_WINDOW[0], "12-31", args.cache_dir),
                extract_weather(sample, args.year, "01-01", WINTER_WINDOW[1], args.cache_dir),
            ]
        )
        summary = wet_summary(wet_dates(s1, daily))
        events = pd.read_parquet(args.processed_dir / f"events_{district}.parquet")
        hit = set(events.loc[events["year"] == args.year, "field_id"])
        summary = summary.assign(district=district, y=summary["field_id"].isin(hit).astype(int))
        rows.append(summary)
    allf = pd.concat(rows)
    allf["any_wet"] = allf["n_wet"] > 0
    by = allf.groupby("district").agg(
        fields=("field_id", "size"),
        wet_fields=("any_wet", "sum"),
        wet_share=("wet_share", "mean"),
        event_rate=("y", "mean"),
    )
    print(by.round(3).to_string())
    print("\nspring event rate by winter wet flag:")
    print(allf.groupby("any_wet")["y"].agg(["size", "mean"]).round(3).to_string())


if __name__ == "__main__":
    main()
