"""Append live forecasts to the prospective log and write the scoreboard (US-20, ADR 0020).

``latest.json`` carries ``forecasts`` (rows of field_id, date, horizon_days, risk, level) once
spring scoring runs (US-22); before that this only refreshes an all-pending scoreboard.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from cropews.config import HORIZONS_DAYS
from cropews.forecast_log import COLUMNS, append_log, scoreboard


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, default=Path("web/public/live/latest.json"))
    parser.add_argument("--log", type=Path, required=True, help="CSV on the forecast-log branch")
    parser.add_argument("--outcomes", type=Path, help="parquet: field_id, date, horizon_days, y")
    parser.add_argument("--out", type=Path, default=Path("web/public/live/scoreboard.json"))
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    rows = (
        json.loads(args.payload.read_text()).get("forecasts", []) if args.payload.exists() else []
    )
    if rows:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: UP017
        log = append_log(args.log, pd.DataFrame(rows).assign(issued_at=stamp))
    elif args.log.exists():
        log = pd.read_csv(args.log, dtype={"field_id": str})
    else:
        log = pd.DataFrame(columns=COLUMNS)
    outcomes = (
        pd.read_parquet(args.outcomes)
        if args.outcomes and args.outcomes.exists()
        else pd.DataFrame(columns=["field_id", "date", "horizon_days", "y"])
    )
    board = scoreboard(log, outcomes, args.today)
    board["horizons"] = {str(h): board["horizons"].get(str(h)) for h in HORIZONS_DAYS}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(board))
    print(f"log: {len(log)} forecasts ({len(rows)} new); wrote {args.out}")


if __name__ == "__main__":
    main()
