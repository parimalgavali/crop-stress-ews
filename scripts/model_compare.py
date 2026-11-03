"""Paired comparison of two score files on identical rows (review finding 4.7).

Both inputs must be parquet with field_id, year, date, horizon_days, y and a score column.
Rows are inner-joined on the keys so both models see the same evaluation set; whole fields
are resampled together and the CI of the AUROC difference is reported per horizon.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cropews.evaluation import paired_auroc_diff

KEY = ["field_id", "year", "date", "horizon_days"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a", type=Path, required=True, help="score parquet (challenger)")
    parser.add_argument("--b", type=Path, required=True, help="score parquet (baseline)")
    parser.add_argument("--score-a", default="score")
    parser.add_argument("--score-b", default="score")
    parser.add_argument("--n", type=int, default=500)
    args = parser.parse_args()

    a = pd.read_parquet(args.a)[["y", *KEY]].assign(score_a=pd.read_parquet(args.a)[args.score_a])
    b = pd.read_parquet(args.b)[KEY].assign(score_b=pd.read_parquet(args.b)[args.score_b])
    m = a.merge(b, on=KEY, how="inner")
    out = {"rows": len(m), "fields": int(m["field_id"].nunique()), "horizons": {}}
    for h, g in m.groupby("horizon_days"):
        d, lo, hi = paired_auroc_diff(g, "score_a", "score_b", n=args.n)
        out["horizons"][str(int(h))] = {
            "diff": round(d, 4),
            "ci": [round(lo, 4), round(hi, 4)],
            "significant": bool(lo > 0 or hi < 0),
        }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
