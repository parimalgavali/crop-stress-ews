"""Extract NRW parcel files per year from the Europe-LAND Zenodo zip (HTTP range requests)."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from remotezip import RemoteZip

from cropews.config import EUROPE_LAND_MEMBER, EUROPE_LAND_NRW_URL, SEASONS


def extract(year: int, out_dir: Path) -> Path:
    member = EUROPE_LAND_MEMBER.format(year=year)
    with RemoteZip(EUROPE_LAND_NRW_URL) as archive:
        archive.extract(member, out_dir)
    return out_dir / member


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=list(SEASONS))
    parser.add_argument("--out", type=Path, default=Path("data/raw/iacs"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(len(args.years)) as pool:
        for path in pool.map(lambda y: extract(y, args.out), args.years):
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
