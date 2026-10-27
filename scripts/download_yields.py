"""Download IT.NRW district crop yields (Landesdatenbank 41241-03i, dl-de/by-2-0)."""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from cropews.data.yields import YIELD_TABLE_URL, parse_district_yields


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/raw/yields/41241-03i_00.csv"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(YIELD_TABLE_URL, timeout=300) as resp:
        args.out.write_bytes(resp.read())
    yields = parse_district_yields(args.out)
    print(f"wrote {args.out}: {len(yields)} district-years {yields.year.min()}-{yields.year.max()}")


if __name__ == "__main__":
    main()
