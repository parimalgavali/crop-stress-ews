"""Fit the training-only baseline, find stress events and write onset targets per grid row."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cropews.config import HORIZONS_DAYS, SPLITS
from cropews.labels import (
    clear_observations,
    find_events,
    fit_baseline,
    fit_peer_scale,
    make_targets,
    peer_residuals,
    score,
    score_peer,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district", default="Soest")
    parser.add_argument("--interim-dir", type=Path, default=Path("data/interim"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--reference", choices=("peer", "climatology"), default="peer")
    args = parser.parse_args()

    files = sorted((args.interim_dir / "s2").glob(f"s2_{args.district}_*.parquet"))
    if not files:
        raise SystemExit(f"no Sentinel-2 files for {args.district!r}")
    s2 = pd.concat(pd.read_parquet(f) for f in files).assign(district=args.district)
    obs = clear_observations(s2)
    if args.reference == "peer":
        residuals = peer_residuals(obs)
        baseline = fit_peer_scale(residuals, SPLITS["train"])
        scored = score_peer(residuals, baseline)
    else:
        baseline = fit_baseline(obs, SPLITS["train"])
        scored = score(obs, baseline)
    events = find_events(scored)

    args.processed_dir.mkdir(parents=True, exist_ok=True)
    events.to_parquet(args.processed_dir / f"events_{args.district}.parquet", index=False)
    fields = s2.groupby("year")["field_id"].nunique()
    with_event = events.groupby("year")["field_id"].nunique()
    summary = pd.DataFrame({"fields": fields, "fields_with_event": with_event}).fillna(0)
    summary["share"] = (summary["fields_with_event"] / summary["fields"]).round(2)
    print(f"{args.reference}: {len(baseline)} (district, 10-day bin) cells from {SPLITS['train']}")
    print(summary.to_string())

    for grid_path in sorted(args.processed_dir.glob(f"grid_{args.district}_*.parquet")):
        grid = pd.read_parquet(grid_path, columns=["field_id", "year", "date"])
        targets = make_targets(grid, events, scored)
        out = grid_path.with_name(grid_path.name.replace("grid_", "labels_"))
        targets.to_parquet(out, index=False)
        rates = {f"{h}d": f"{targets[f'onset_{h}d'].mean():.1%}" for h in HORIZONS_DAYS}
        print(f"wrote {out}: {len(targets)} rows; positive rate {rates}")


if __name__ == "__main__":
    main()
