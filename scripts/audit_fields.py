"""Count winter-wheat fields and hectares per season and district."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

from cropews.config import EUROPE_LAND_MEMBER, SEASONS
from cropews.data.fields import assign_districts, load_winter_wheat_fields


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iacs-dir", type=Path, default=Path("data/raw/iacs"))
    parser.add_argument("--districts", type=Path, required=True, help="BKG VG250/VG2500 KRS layer")
    parser.add_argument("--out", type=Path, default=Path("outputs/wheat_by_district.csv"))
    args = parser.parse_args()

    districts = gpd.read_file(args.districts)
    districts = districts[districts["ARS"].str.startswith("05")]
    rows = []
    for year in SEASONS:
        path = args.iacs_dir / EUROPE_LAND_MEMBER.format(year=year)
        fields = load_winter_wheat_fields(path, year)
        fields = assign_districts(fields, districts)
        print(f"{year}: {len(fields)} fields, {fields['field_size'].sum():,.0f} ha")
        summary = fields.groupby("district").agg(
            fields=("field_id", "count"), ha=("field_size", "sum")
        )
        rows.append(summary.reset_index().assign(year=year))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(rows).to_csv(args.out, index=False)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
