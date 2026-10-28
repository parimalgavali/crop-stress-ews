"""Send ntfy.sh alerts for Live fields that turned red since the previous run (ADR 0022)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cropews.alerts import new_red, send, topic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", type=Path, default=Path("web/public/live/latest.json"))
    parser.add_argument("--previous", type=Path, help="latest.json of the last deployed run")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cur = json.loads(args.current.read_text())
    prev = None
    if args.previous is not None and args.previous.is_file():
        prev = json.loads(args.previous.read_text())
    alerts = new_red(prev, cur)
    for fid, h in alerts:
        print(f"{topic(fid)}: red at {h['days']} d")
    if not args.dry_run:
        print(f"sent {send(alerts, cur['as_of'])} of {len(alerts)} alerts")


if __name__ == "__main__":
    main()
