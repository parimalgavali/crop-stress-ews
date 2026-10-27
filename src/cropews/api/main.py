"""Endpoints: fields in a bbox (GeoJSON) and 7/14/21-day risk with reasons per field/date."""

from __future__ import annotations

import datetime as dt
import json
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cropews.api.db import get_session
from cropews.api.models import Field, Prediction
from cropews.api.schemas import FeatureCollection, FieldRisk, HorizonRisk

MAX_FIELDS = 2000
LEVEL_RANK = {"green": 0, "amber": 1, "red": 2}

app = FastAPI(title="crop-stress-ews", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])
SessionDep = Annotated[Session, Depends(get_session)]


def parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    try:
        minx, miny, maxx, maxy = (float(v) for v in bbox.split(","))
    except ValueError as err:
        raise HTTPException(422, "bbox must be minLon,minLat,maxLon,maxLat") from err
    if minx >= maxx or miny >= maxy:
        raise HTTPException(422, "bbox min must be below max")
    return minx, miny, maxx, maxy


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/dates", response_model=list[dt.date])
def dates(session: SessionDep, year: int) -> list[dt.date]:
    rows = session.scalars(
        select(Prediction.date).where(Prediction.year == year).distinct().order_by(Prediction.date)
    )
    return list(rows)


@app.get("/fields", response_model=FeatureCollection)
def fields(
    session: SessionDep,
    bbox: Annotated[str, Query(description="minLon,minLat,maxLon,maxLat (EPSG:4326)")],
    year: int,
    date: dt.date | None = None,
) -> FeatureCollection:
    """Fields intersecting ``bbox``; with ``date``, ``level`` is the worst level over horizons."""
    envelope = func.ST_MakeEnvelope(*parse_bbox(bbox), 4326)
    rows = session.execute(
        select(Field.field_id, Field.district, Field.area_ha, func.ST_AsGeoJSON(Field.geom, 6))
        .where(Field.year == year, func.ST_Intersects(Field.geom, envelope))
        .limit(MAX_FIELDS)
    ).all()
    levels: dict[str, str] = {}
    if date is not None and rows:
        preds = session.execute(
            select(Prediction.field_id, Prediction.level).where(
                Prediction.year == year,
                Prediction.date == date,
                Prediction.field_id.in_([r[0] for r in rows]),
            )
        )
        for fid, lvl in preds:
            if LEVEL_RANK[lvl] >= LEVEL_RANK.get(levels.get(fid, "green"), 0):
                levels[fid] = lvl
    features = [
        {
            "type": "Feature",
            "id": fid,
            "geometry": json.loads(geom),
            "properties": {
                "field_id": fid,
                "district": district,
                "area_ha": area,
                "level": levels.get(fid),
            },
        }
        for fid, district, area, geom in rows
    ]
    return FeatureCollection(features=features)


@app.get("/fields/{field_id}/risk", response_model=FieldRisk)
def field_risk(session: SessionDep, field_id: str, year: int, date: dt.date) -> FieldRisk:
    field = session.get(Field, (field_id, year))
    if field is None:
        raise HTTPException(404, "field not found")
    preds = session.scalars(
        select(Prediction)
        .where(Prediction.field_id == field_id, Prediction.year == year, Prediction.date == date)
        .order_by(Prediction.horizon_days)
    ).all()
    if not preds:
        raise HTTPException(404, "no prediction for this date")
    return FieldRisk(
        field_id=field_id,
        year=year,
        date=date,
        district=field.district,
        horizons=[
            HorizonRisk.model_validate(
                {"days": p.horizon_days, "risk": p.risk, "level": p.level, "reasons": p.reasons}
            )
            for p in preds
        ],
    )
