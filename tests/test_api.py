"""API tests against a real PostGIS (``DATABASE_URL``); skipped when it is not reachable."""

import datetime as dt

import pytest

pytest.importorskip("fastapi")
sqlalchemy = pytest.importorskip("sqlalchemy")

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from geoalchemy2.shape import from_shape  # noqa: E402
from shapely.geometry import box  # noqa: E402

from cropews.api.db import SessionLocal, engine  # noqa: E402
from cropews.api.main import app  # noqa: E402
from cropews.api.models import Field, Prediction  # noqa: E402

DAY = dt.date(2024, 5, 10)
REASON = [{"code": "dry_spell", "text_en": "Little rain", "text_de": "Wenig Regen"}]


@pytest.fixture(scope="module")
def client():
    try:
        with engine.connect():
            pass
    except sqlalchemy.exc.OperationalError:
        pytest.skip("PostGIS not reachable at DATABASE_URL")
    command.upgrade(Config("alembic.ini"), "head")
    with SessionLocal.begin() as s:
        s.query(Prediction).delete()
        s.query(Field).delete()
        for fid, x0 in (("a", 8.0), ("b", 9.0)):
            s.add(
                Field(
                    field_id=fid,
                    year=2024,
                    district="Soest",
                    area_ha=3.0,
                    geom=from_shape(box(x0, 51.5, x0 + 0.01, 51.51), srid=4326),
                )
            )
        s.flush()
        for h, lvl in ((7, "green"), (14, "amber"), (21, "red")):
            s.add(
                Prediction(
                    field_id="a",
                    year=2024,
                    date=DAY,
                    horizon_days=h,
                    risk=h / 100,
                    level=lvl,
                    reasons=REASON,
                )
            )
    yield TestClient(app)


def test_fields_in_bbox_with_worst_level(client):
    r = client.get("/fields", params={"bbox": "7.9,51.4,8.5,51.6", "year": 2024, "date": DAY})
    assert r.status_code == 200
    feats = r.json()["features"]
    assert [f["id"] for f in feats] == ["a"]
    assert feats[0]["properties"]["level"] == "red"
    assert feats[0]["geometry"]["type"] == "Polygon"


def test_bad_bbox_is_rejected(client):
    assert client.get("/fields", params={"bbox": "1,2,3", "year": 2024}).status_code == 422
    assert client.get("/fields", params={"bbox": "9,51,8,52", "year": 2024}).status_code == 422


def test_risk_per_horizon_with_reasons(client):
    r = client.get("/fields/a/risk", params={"year": 2024, "date": DAY})
    assert r.status_code == 200
    body = r.json()
    assert [h["days"] for h in body["horizons"]] == [7, 14, 21]
    assert body["horizons"][2]["level"] == "red"
    assert body["horizons"][0]["reasons"][0]["code"] == "dry_spell"


def test_missing_field_or_date_is_404(client):
    assert client.get("/fields/zzz/risk", params={"year": 2024, "date": DAY}).status_code == 404
    r = client.get("/fields/b/risk", params={"year": 2024, "date": DAY})
    assert r.status_code == 404


def test_dates(client):
    assert client.get("/dates", params={"year": 2024}).json() == [DAY.isoformat()]
