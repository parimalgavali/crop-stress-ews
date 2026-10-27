from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel

Level = Literal["green", "amber", "red"]


class Reason(BaseModel):
    code: str
    text_en: str
    text_de: str


class HorizonRisk(BaseModel):
    days: int
    risk: float
    level: Level
    reasons: list[Reason]


class FieldRisk(BaseModel):
    field_id: str
    year: int
    date: dt.date
    district: str
    horizons: list[HorizonRisk]


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[dict[str, Any]]
