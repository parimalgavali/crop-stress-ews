"""Load ``fields.geoparquet`` and ``predictions.parquet`` (from export_predictions.py) into PostGIS.

Replaces existing rows. Run ``alembic upgrade head`` first.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from geoalchemy2.shape import from_shape
from sqlalchemy import delete, insert

from cropews.api.db import SessionLocal
from cropews.api.models import Field, Prediction


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("data/outputs"))
    args = parser.parse_args()
    fields = gpd.read_parquet(args.out_dir / "fields.geoparquet").to_crs("EPSG:4326")
    preds = pd.read_parquet(args.out_dir / "predictions.parquet")
    with SessionLocal.begin() as session:
        session.execute(delete(Prediction))
        session.execute(delete(Field))
        session.execute(
            insert(Field),
            [
                {
                    "field_id": str(r.field_id),
                    "year": int(r.year),
                    "district": r.district,
                    "area_ha": float(r.area_ha),
                    "geom": from_shape(r.geometry, srid=4326),
                }
                for r in fields.itertuples()
            ],
        )
        session.execute(
            insert(Prediction),
            [
                {
                    "field_id": str(r.field_id),
                    "year": int(r.year),
                    "date": pd.Timestamp(r.date).date(),
                    "horizon_days": int(r.horizon_days),
                    "risk": float(r.risk),
                    "level": r.level,
                    "reasons": json.loads(r.reasons),
                }
                for r in preds.itertuples()
            ],
        )
    print(f"loaded {len(fields)} field-seasons and {len(preds)} predictions")


if __name__ == "__main__":
    main()
