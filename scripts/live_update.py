"""Live season update (ADR 0015): current conditions for a fixed sample of arable LWK parcels.

Writes web/public/live/latest.json for the Pages build; .github/workflows/pages.yml runs it
every 5 days.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

from cropews.config import CORE_DISTRICTS, PREDICTION_WINDOW
from cropews.cropmap import predict, season_start
from cropews.data.fields import assign_districts, stable_sample
from cropews.data.forecast import live_forecast
from cropews.data.lwk import LWK_ATTRIBUTION, load_arable_parcels
from cropews.data.sentinel1 import extract_backscatter_series
from cropews.data.sentinel2 import extract_field_series
from cropews.data.weather import extract_weather
from cropews.live import (
    WHEAT_THRESHOLD,
    cache_since,
    conditions,
    forecast_summary,
    live_payload,
    merge_cached,
    run_health,
    season_series,
)
from cropews.live_risk import load_bundle, score_live, spring_active
from cropews.winter import live_winter

ATTRIBUTION = (
    f"Parcels: {LWK_ATTRIBUTION}. Weather: DWD Climate Data Center, CC BY 4.0. "
    "Forecast: DWD ICON via Open-Meteo, CC BY 4.0. Contains modified Copernicus Sentinel data."
)
WEATHER_LAG_DAYS = 2
Cache = tuple[dict | None, pd.DataFrame | None, pd.DataFrame | None]


def _load_cache(path: Path | None) -> Cache:
    """Satellite observations of earlier runs (ADR 0025); empty if absent or unreadable."""
    try:
        assert path is not None
        meta = json.loads((path / "meta.json").read_text())
        return meta, pd.read_parquet(path / "s2.parquet"), pd.read_parquet(path / "s1.parquet")
    except Exception:  # noqa: BLE001 - any problem means a full extraction, which is always valid
        return None, None, None


def _save_cache(path: Path, s2: pd.DataFrame, s1: pd.DataFrame, meta: dict) -> None:
    path.mkdir(parents=True, exist_ok=True)
    s2.to_parquet(path / "s2.parquet", index=False)
    s1.to_parquet(path / "s1.parquet", index=False)
    (path / "meta.json").write_text(json.dumps(meta))


def _window_start(as_of: date, days: int, whole_season: bool) -> date:
    first_image = as_of - timedelta(days)
    return min(first_image, season_start(as_of)) if whole_season else first_image


def _district(job: tuple[gpd.GeoDataFrame, date, int, bool, Cache]) -> tuple[pd.DataFrame, ...]:
    fields, as_of, days, whole_season, (meta, c2, c1) = job
    start = _window_start(as_of, days, whole_season)
    ids = set(fields["field_id"])
    since = cache_since(meta, ids, start, as_of).isoformat()
    s2 = extract_field_series(fields, since, as_of.isoformat())
    s2 = merge_cached(c2, s2, ids, start, as_of, ["field_id", "date"])
    s1 = extract_backscatter_series(fields, since, as_of.isoformat())
    s1 = merge_cached(c1, s1, ids, start, as_of, ["field_id", "date", "orbit_state"])
    end = as_of - timedelta(WEATHER_LAG_DAYS)
    first = as_of - timedelta(days)
    if spring_active(as_of):
        first = min(first, date.fromisoformat(f"{as_of.year}-{PREDICTION_WINDOW[0]}"))
    frames = []
    for year in range(first.year, end.year + 1):
        lo = max(first, date(year, 1, 1)).strftime("%m-%d")
        hi = min(end, date(year, 12, 31)).strftime("%m-%d")
        frames.append(extract_weather(fields, year, lo, hi, ambav=False))
    return s2, s1, pd.concat(frames, ignore_index=True)


def _forecasts(fields: gpd.GeoDataFrame, as_of: date) -> dict[str, dict[str, object]]:
    """ICON 5-day summary at each district's field centroid; empty if the service fails."""
    out: dict[str, dict[str, object]] = {}
    for district, g in fields.groupby("district"):
        c = g.to_crs(4326).geometry.union_all().centroid
        try:
            out[str(district)] = forecast_summary(live_forecast(c.y, c.x), as_of)
        except (requests.RequestException, RuntimeError, KeyError) as err:
            print(f"forecast {district}: {err}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lwk", type=Path, required=True, help="V_OD_LWK_TSCHLAG.shp")
    parser.add_argument("--districts", type=Path, required=True, help="BKG VG2500 KRS layer")
    parser.add_argument("--n", type=int, default=60, help="parcels per district")
    parser.add_argument("--cache", type=Path, help="observation cache dir (ADR 0025)")
    parser.add_argument("--days", type=int, default=60, help="look-back window")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--workers", type=int, default=len(CORE_DISTRICTS))
    parser.add_argument("--out", type=Path, default=Path("web/public/live/latest.json"))
    parser.add_argument(
        "--risk-model", type=Path, help="risk_live.joblib, spring risk from 5 April (ADR 0021)"
    )
    parser.add_argument(
        "--cropmap", type=Path, help="directory with cropmap_y_wheat_<cutoff>.joblib (ADR 0018)"
    )
    args = parser.parse_args()
    started = time.monotonic()

    use_map = args.cropmap is not None and args.cropmap.is_dir()
    season = f"{season_start(args.as_of).year}/{season_start(args.as_of).year + 1}"
    parcels = assign_districts(load_arable_parcels(args.lwk), gpd.read_file(args.districts))
    sets = [
        stable_sample(parcels[parcels["district"] == d], args.n, season).assign(district=d)
        for d in CORE_DISTRICTS
    ]
    cache = _load_cache(args.cache)
    with ProcessPoolExecutor(args.workers) as pool:
        jobs = [(f, args.as_of, args.days, use_map, cache) for f in sets]
        results = list(pool.map(_district, jobs))
    skipped = {
        k: [x for r in results for x in r[i].attrs.get("skipped_scenes", [])]
        for k, i in (("s2", 0), ("s1", 1))
    }
    s2, s1, daily = (pd.concat([r[i] for r in results], ignore_index=True) for i in range(3))
    fields = gpd.GeoDataFrame(pd.concat(sets, ignore_index=True), crs=parcels.crs)
    if args.cache is not None:
        start = _window_start(args.as_of, args.days, use_map)
        meta = {"start": start.isoformat(), "through": args.as_of.isoformat()}
        _save_cache(args.cache, s2, s1, meta | {"fields": sorted(fields["field_id"])})
    wheat_p = predict(args.cropmap, args.as_of, s1, s2) if use_map else None
    cond = conditions(s2, s1, daily, args.as_of)
    bundle = load_bundle(args.risk_model) if spring_active(args.as_of) else None
    risk, rows = {}, []
    if bundle is not None:
        scored = fields
        if wheat_p is not None:
            scored = fields[fields["field_id"].map(wheat_p).fillna(0) >= WHEAT_THRESHOLD]
        ids = scored.set_index("field_id")["district"]
        risk, rows = score_live(bundle, ids, s2, s1, daily, args.as_of)
    winter = {}
    cereals = fields.iloc[:0]
    if wheat_p is not None:
        cereals = fields[fields["field_id"].map(wheat_p).fillna(0) >= WHEAT_THRESHOLD]
        winter = live_winter(s2, s1, daily, cereals.set_index("field_id")["district"], args.as_of)
    district = fields.set_index("field_id")["district"]
    peer_ids = set(cereals["field_id"]) if wheat_p is not None else set(district.index)
    season_chart = season_series(s2, district, peer_ids, args.as_of)
    season_chart["peer_kind"] = "cereal" if wheat_p is not None else "all"
    payload = live_payload(
        fields,
        cond,
        args.as_of,
        ATTRIBUTION,
        wheat_p,
        _forecasts(fields, args.as_of),
        risk,
        rows,
        winter,
        season_chart,
    )

    payload["health"] = run_health(
        len(fields),
        len(payload["conditions"]),
        skipped["s1"],
        skipped["s2"],
        time.monotonic() - started,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    n = len(payload["conditions"])
    print(f"wrote {args.out}: {len(fields)} parcels, {n} with data, {len(risk)} scored")


if __name__ == "__main__":
    main()
