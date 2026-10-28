"""Exit 1 if the live payload is missing or mostly empty (ADR 0023); prints a one-line summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cropews.live import health_problem


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("latest", type=Path, help="web/public/live/latest.json")
    args = parser.parse_args()
    payload = json.loads(args.latest.read_text()) if args.latest.is_file() else None
    problem = health_problem(payload)
    if problem:
        print(problem)
        return 1
    assert payload is not None
    h = payload.get("health", {})
    skipped = len(h.get("s1_scenes_skipped", [])) + len(h.get("s2_scenes_skipped", []))
    print(
        f"as of {payload['as_of']}: {len(payload['conditions'])} of "
        f"{len(payload['fields']['features'])} parcels with data, "
        f"{skipped} satellite scenes skipped, {h.get('minutes', '?')} min"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
