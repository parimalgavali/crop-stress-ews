"""Export calibrated risk, traffic-light level and reasons for the demo seasons (ADR 0012).

Fits the US-08 logistic model per horizon on training seasons, Platt-calibrates it on validation,
sets red/amber at 90%/75% validation specificity, and scores the test and extra-check seasons
where the horizon ends by the senescence cutoff (where labels are defined).
Writes ``predictions.parquet`` and ``fields.geoparquet`` (EPSG:4326) for ``scripts/load_db.py``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from cropews.baselines import logistic_model
from cropews.config import EUROPE_LAND_MEMBER, HORIZONS_DAYS
from cropews.dataset import load_feature_table
from cropews.evaluation import threshold_at_specificity
from cropews.explain import contributions, level, top_reasons
from cropews.features import feature_columns
from cropews.labels import SENESCENCE_CUTOFF

DEMO_SPLITS = ("test", "extra_check")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--iacs-dir", type=Path, default=Path("data/raw/iacs"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/outputs"))
    args = parser.parse_args()

    data = load_feature_table(args.processed_dir)
    cols = [c for c in feature_columns(data) if not c.startswith("onset_")]
    cols = [c for c in cols if c not in ("in_event", "split")]
    demo = data[data["split"].isin(DEMO_SPLITS)].reset_index(drop=True)
    frames = []
    for h in HORIZONS_DAYS:
        target = f"onset_{h}d"
        d = data.dropna(subset=[target])
        train, val = d[d["split"] == "train"], d[d["split"] == "validation"]
        model = logistic_model().fit(train[cols], train[target].astype(int))
        platt = LogisticRegression().fit(
            model.decision_function(val[cols]).reshape(-1, 1), val[target].astype(int)
        )
        val_risk = platt.predict_proba(model.decision_function(val[cols]).reshape(-1, 1))[:, 1]
        y_val = val[target].astype(int).to_numpy()
        red = threshold_at_specificity(y_val, val_risk, 0.90)
        amber = threshold_at_specificity(y_val, val_risk, 0.75)
        cutoff = pd.to_datetime(demo["year"].astype(str) + "-" + SENESCENCE_CUTOFF)
        keep = (demo["date"] + pd.Timedelta(days=h) <= cutoff).to_numpy()
        risk = platt.predict_proba(model.decision_function(demo[cols]).reshape(-1, 1))[:, 1]
        reasons = top_reasons(contributions(model, demo[cols]))
        frames.append(
            demo[["field_id", "year", "date"]]
            .assign(
                horizon_days=h,
                risk=np.round(risk, 4),
                level=level(risk, amber, red),
                reasons=[json.dumps(r, ensure_ascii=False) for r in reasons],
            )
            .loc[keep]
        )
        print(f"{h:>2}d amber ≥ {amber:.3f} red ≥ {red:.3f}")
    preds = pd.concat(frames, ignore_index=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(args.out_dir / "predictions.parquet", index=False)
    print(preds.groupby(["year", "horizon_days"])["level"].value_counts().unstack().to_string())

    keys = demo[["field_id", "year", "district"]].drop_duplicates()
    fields = []
    for year, ids in keys.groupby("year"):
        path = args.iacs_dir / EUROPE_LAND_MEMBER.format(year=year)
        g = gpd.read_parquet(path, columns=["field_id", "field_size", "geometry"])
        g = g[g["field_id"].isin(ids["field_id"])].merge(ids, on="field_id")
        fields.append(g.rename(columns={"field_size": "area_ha"}).to_crs("EPSG:4326"))
    out = gpd.GeoDataFrame(pd.concat(fields, ignore_index=True), crs="EPSG:4326")
    out.to_parquet(args.out_dir / "fields.geoparquet", index=False)
    print(f"wrote {len(preds)} predictions for {len(out)} field-seasons to {args.out_dir}")


if __name__ == "__main__":
    main()
