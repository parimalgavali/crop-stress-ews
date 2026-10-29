"""Does a soil-moisture forecast help the Live risk model? (US-34, ADR 0031)

The Live model dropped DWD AMBAV soil moisture (monthly, ADR 0021). Open-Meteo has a daily
soil-moisture forecast at 0–7 and 7–28 cm. Its archive covers the training years only as ERA5
reanalysis, so: train with ERA5 at each district's field centroid (the next-5-day change is a
perfect forecast), compare on 2022 (ADR 0008), and also on 2024 and 2025.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from cropews.baselines import logistic_model
from cropews.config import HORIZONS_DAYS
from cropews.data.forecast import archived_soil_moisture, soil_moisture_features
from cropews.dataset import load_feature_table
from cropews.evaluation import bootstrap_ci
from cropews.features import feature_columns

AMBAV_FEATURES = ("water_balance_30d", "soil_moist_pct")
SM = ["sm_top", "sm_root", "sm_root_change_5d"]


def centroids(data: pd.DataFrame, iacs: Path) -> dict[str, tuple[float, float]]:
    frames = []
    for year, g in data.groupby("year"):
        f = gpd.read_parquet(
            iacs / f"GSA-DE_NRW-{year}.geoparquet", columns=["field_id", "geometry"]
        )
        ids = g[["field_id", "district"]].drop_duplicates()
        frames.append(f.merge(ids, on="field_id").to_crs(4326))
    fields = gpd.GeoDataFrame(pd.concat(frames), crs=4326)
    out = {}
    for district, g in fields.groupby("district"):
        c = g.geometry.union_all().centroid
        out[str(district)] = (c.y, c.x)
    return out


def era5(data: pd.DataFrame, iacs: Path, cache: Path) -> pd.DataFrame:
    if cache.exists():
        return pd.read_parquet(cache)
    years = sorted(data["year"].unique())
    frames = []
    for district, (lat, lon) in centroids(data, iacs).items():
        daily = archived_soil_moisture(lat, lon, date(years[0], 1, 1), date(years[-1], 12, 31))
        frames.append(soil_moisture_features(daily).assign(district=district))
    out = pd.concat(frames, ignore_index=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(cache, index=False)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--iacs", type=Path, default=Path("data/raw/iacs"))
    parser.add_argument(
        "--cache", type=Path, default=Path("data/interim/era5_soil_moisture.parquet")
    )
    parser.add_argument("--out", type=Path, default=Path("outputs/soil_moisture_eval.json"))
    parser.add_argument("--bootstrap", type=int, default=300)
    args = parser.parse_args()

    data = load_feature_table(args.processed_dir)
    full = [c for c in feature_columns(data) if not c.startswith("onset_")]
    live = [c for c in full if c not in ("in_event", "split", *AMBAV_FEATURES)]
    sm = era5(data, args.iacs, args.cache)
    data = data.merge(sm, on=["district", "date"], how="left")
    report: dict[str, object] = {"missing_share": float(data["sm_root"].isna().mean())}
    variants = {
        "live": live,
        "live+sm_now": live + SM[:2],
        "live+sm_now+5d": live + SM,
        "full_ambav": live + list(AMBAV_FEATURES),
    }
    for h in HORIZONS_DAYS:
        t = f"onset_{h}d"
        d = data.dropna(subset=[t]).assign(y=lambda x, t=t: x[t].astype(int))
        train = d[d["split"] == "train"]
        row: dict[str, object] = {}
        for name, cols in variants.items():
            model = logistic_model().fit(train[cols], train["y"])
            for s in ("validation", "test", "extra_check"):
                ev = d[d["split"] == s]
                ev = ev.assign(score=model.decision_function(ev[cols]))
                row[f"{name}/{s}"] = {
                    "auroc": round(float(roc_auc_score(ev["y"], ev["score"])), 3),
                    "ci": bootstrap_ci(
                        ev, lambda x: float(roc_auc_score(x["y"], x["score"])), n=args.bootstrap
                    ),
                }
        report[f"{h}d"] = row
        print(f"{h:>2}d " + "  ".join(f"{k} {v['auroc']:.3f}" for k, v in row.items()))  # type: ignore[index]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=lambda v: np.asarray(v).tolist()))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
