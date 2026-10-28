# Week 19 — Soil from the NRW soil map (US-33)

- What: each Live card names the field's soil (BK50) and says in plain words whether it holds
  water, has groundwater close to the surface, or tends to stay wet. Soil was also tested as a
  risk-model input (ADR 0030).
- Why: soil explains waterlogging and dry-spell stress. A tested and rejected input is also a
  result.
- Verify: `PYTHONPATH=src python -m pytest -q tests/test_soil.py`; in `web/`, `npm test`; for the
  experiment, from `scripts/`, `PYTHONPATH=../src python soil_eval.py --processed-dir ../data/processed --iacs ../data/raw/iacs --cache ../data/interim/soil.parquet`.
- Result: no gain on the 2022 validation season, so the model is unchanged.
- Out of scope: using soil in the model, the full 640 MB GeoPackage.
