from __future__ import annotations

import datetime as dt
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import Date, Float, ForeignKeyConstraint, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Field(Base):
    __tablename__ = "fields"
    field_id: Mapped[str] = mapped_column(String, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    district: Mapped[str] = mapped_column(String)
    area_ha: Mapped[float] = mapped_column(Float)
    geom: Mapped[Any] = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=True))


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        ForeignKeyConstraint(["field_id", "year"], ["fields.field_id", "fields.year"]),
        Index("ix_predictions_field_date", "field_id", "year", "date"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_id: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    date: Mapped[dt.date] = mapped_column(Date)
    horizon_days: Mapped[int] = mapped_column(Integer)
    risk: Mapped[float] = mapped_column(Float)
    level: Mapped[str] = mapped_column(String(5))
    reasons: Mapped[list[dict[str, str]]] = mapped_column(JSONB)
