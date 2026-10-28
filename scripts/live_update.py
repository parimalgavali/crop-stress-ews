"""Live season update (ADR 0015): current conditions for a fixed sample of arable LWK parcels.

Writes web/public/live/latest.json for the Pages build; .github/workflows/pages.yml runs it
every 5 days.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import geopandas as gpd
import pandas as pd

from cropews.config import CORE_DISTRICTS
from cropews.data.fields import assign_districts, sample_fields
from cropews.data.lwk import LWK_ATTRIBUTION, load_arable_parcels
from cropews.data.sentinel1 import extract_backscatter_series
from cropews.data.sentinel2 import extract_field_series
from cropews.data.weather import extract_weather
from cropews.live import conditions, live_payload

ATTRIBUTION = (
    f"Parcels: {LWK_ATTRIBUTION}. Weather: DWD Climate Data Center, CC BY 4.0. "
    "Contains modified Copernicus Sentinel data."
)
WEATHER_LAG_DAYS = 2


def _district(job: tuple[gpd.GeoDataFrame, date, int]) -> tuple[pd.DataFrame, ...]:
    fields, as_of, days = job
    start = (as_of - timedelta(days)).isoformat()
    s2 = extract_field_series(fields, start, as_of.isoformat())
    s1 = extract_backscatter_series(fields, start, as_of.isoformat())
    end = as_of - timedelta(WEATHER_LAG_DAYS)
    first = as_of - timedelta(days)
    frames = []
    for year in range(first.year, end.year + 1):
        lo = max(first, date(year, 1, 1)).strftime("%m-%d")
        hi = min(end, date(year, 12, 31)).strftime("%m-%d")
        frames.append(extract_weather(fields, year, lo, hi, ambav=False))
    return s2, s1, pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lwk", type=Path, required=True, help="V_OD_LWK_TSCHLAG.shp")
    parser.add_argument("--districts", type=Path, required=True, help="BKG VG2500 KRS layer")
    parser.add_argument("--n", type=int, default=30, help="parcels per district")
    parser.add_argument("--days", type=int, default=60, help="look-back window")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--workers", type=int, default=len(CORE_DISTRICTS))
    parser.add_argument("--out", type=Path, default=Path("web/public/live/latest.json"))
    args = parser.parse_args()

    parcels = assign_districts(load_arable_parcels(args.lwk), gpd.read_file(args.districts))
    sets = [
        sample_fields(parcels[parcels["district"] == d], args.n).assign(district=d)
        for d in CORE_DISTRICTS
    ]
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(_district, [(f, args.as_of, args.days) for f in sets]))
    s2, s1, daily = (pd.concat([r[i] for r in results], ignore_index=True) for i in range(3))
    fields = gpd.GeoDataFrame(pd.concat(sets, ignore_index=True), crs=parcels.crs)
    payload = live_payload(fields, conditions(s2, s1, daily, args.as_of), args.as_of, ATTRIBUTION)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    n = len(payload["conditions"])
    print(f"wrote {args.out}: {len(fields)} parcels, {n} with data, as of {args.as_of}")


if __name__ == "__main__":
    main()
