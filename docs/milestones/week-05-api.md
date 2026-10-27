# Week 5 — API and PostGIS (US-10)

## What was done

FastAPI service over precomputed, calibrated 7/14/21-day risk with traffic-light levels and
plain-language EN/DE reasons; PostGIS schema via Alembic; `docker compose up` for API + DB
([ADR 0012](../decisions/0012-api-and-demo-model.md), [api.md](../api.md)).

## Why

The UI (US-11) and replay demo need one backend that serves exactly the evaluated predictions.

## How to verify

`pytest -q` with `DATABASE_URL` pointing to a PostGIS (CI does this); or the commands in
[api.md](../api.md) and `curl localhost:8000/health`.

## Out of scope / next

Six-district export once Sentinel-1 is complete; US-11 one-screen UI.
