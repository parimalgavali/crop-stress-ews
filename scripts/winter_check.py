"""Winter emergence check on past seasons (ADR 0016): does weak winter cover precede spring stress?

Reads data/interim/s2w/s2_<district>_<year>_winter.parquet and
data/processed/events_<district>.parquet.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cropews.config import CORE_DISTRICTS, SPLITS
from cropews.winter import emergence_scores, spring_outcome, summarise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s2w-dir", type=Path, default=Path("data/interim/s2w"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    s2 = pd.concat(
        pd.read_parquet(p).assign(district=d)
        for d in CORE_DISTRICTS
        for p in sorted(args.s2w_dir.glob(f"s2_{d}_*_winter.parquet"))
    )
    events = pd.concat(
        pd.read_parquet(args.processed_dir / f"events_{d}.parquet") for d in CORE_DISTRICTS
    )
    scores = spring_outcome(emergence_scores(s2, SPLITS["train"]), events)
    rows = []
    for split, years in SPLITS.items():
        part = scores[scores["year"].isin(years)]
        if len(part):
            rows.append({"split": split, **summarise(part)})
    table = pd.DataFrame(rows)
    print(table.round(2).to_string(index=False))
    print("\nper season (all splits):")
    per_year = scores.groupby("year")[list(scores.columns)].apply(lambda g: pd.Series(summarise(g)))
    print(per_year.round(2).to_string())


if __name__ == "__main__":
    main()
