"""Validate an interchange document against the cropews contract.

Usage:
    python scripts/import_validate.py <file> [--kind fields|scores|observations|adapter]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cropews.interchange import (  # noqa: E402
    ContractError,
    adapt_simulated_export,
    import_fields_geojson,
    import_observations,
    import_scores_csv,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    ap.add_argument("--kind", choices=["fields", "scores", "observations", "adapter"])
    args = ap.parse_args()
    text = args.file.read_text()
    try:
        if args.kind == "adapter":
            adapted = adapt_simulated_export(text)
            df = import_fields_geojson(adapted)
            print(f"adapter OK: {len(df)} fields mapped into cropews-fields")
            return
        fn = {
            "fields": import_fields_geojson,
            "scores": import_scores_csv,
            "observations": import_observations,
        }[args.kind or ""]
        df = fn(text)
        print(f"{args.kind} OK: {len(df)} rows")
    except ContractError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
