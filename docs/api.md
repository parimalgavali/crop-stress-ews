# API (US-10)

Design: [ADR 0012](decisions/0012-api-and-demo-model.md). Code: `src/cropews/api/`,
`src/cropews/explain.py`, `migrations/`, `scripts/export_predictions.py`, `scripts/load_db.py`.

```bash
python scripts/export_predictions.py          # -> data/outputs/{predictions.parquet,fields.geoparquet}
docker compose up -d --build                  # PostGIS + API on :8000, runs alembic upgrade head
docker compose exec api python scripts/load_db.py
```

| Endpoint | Returns |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `GET /dates?year=2024` | dates with predictions |
| `GET /fields?bbox=minLon,minLat,maxLon,maxLat&year=2024[&date=2024-05-10]` | GeoJSON fields; `level` = worst horizon on that date |
| `GET /fields/{field_id}/risk?year=2024&date=2024-05-10` | risk, level and up to 2 reasons per horizon |

Example `/fields/{id}/risk` response (shape):

```json
{"field_id": "…", "year": 2024, "date": "2024-05-10", "district": "Soest",
 "horizons": [{"days": 7, "risk": 0.08, "level": "red",
   "reasons": [{"code": "behind_neighbours", "text_en": "Crop is behind neighbouring fields",
                "text_de": "Bestand liegt hinter den Nachbarfeldern"}]}, …]}
```

Soest export (2024 + 2025, 40 fields each, 3,600 rows): 7-day level shares in 2024 are
82% green, 9% amber, 10% red.

Tests: `tests/test_explain.py` (reason mapping, levels, reasons follow the driving feature) and
`tests/test_api.py` (needs `DATABASE_URL` to a PostGIS; CI provides one, skipped otherwise).
