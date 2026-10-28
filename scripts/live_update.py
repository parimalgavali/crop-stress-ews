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
from cropews.cropmap import predict, season_start
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


def _district(job: tuple[gpd.GeoDataFrame, date, int, bool]) -> tuple[pd.DataFrame, ...]:
    fields, as_of, days, whole_season = job
    first_image = as_of - timedelta(days)
    if whole_season:
        first_image = min(first_image, season_start(as_of))
    start = first_image.isoformat()
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
    parser.add_argument(
        "--cropmap", type=Path, help="models/cropmap_y_wheat.joblib; images from 1 Oct (ADR 0018)"
    )
    args = parser.parse_args()

    use_map = args.cropmap is not None and args.cropmap.exists()
    parcels = assign_districts(load_arable_parcels(args.lwk), gpd.read_file(args.districts))
    sets = [
        sample_fields(parcels[parcels["district"] == d], args.n).assign(district=d)
        for d in CORE_DISTRICTS
    ]
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(_district, [(f, args.as_of, args.days, use_map) for f in sets]))
    s2, s1, daily = (pd.concat([r[i] for r in results], ignore_index=True) for i in range(3))
    fields = gpd.GeoDataFrame(pd.concat(sets, ignore_index=True), crs=parcels.crs)
    wheat_p = predict(args.cropmap, s1, s2) if use_map else None
    cond = conditions(s2, s1, daily, args.as_of)
    payload = live_payload(fields, cond, args.as_of, ATTRIBUTION, wheat_p)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    n = len(payload["conditions"])
    print(f"wrote {args.out}: {len(fields)} parcels, {n} with data, as of {args.as_of}")


if __name__ == "__main__":
    main()
