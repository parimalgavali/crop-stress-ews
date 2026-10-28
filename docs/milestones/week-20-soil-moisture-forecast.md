# Week 20 — Soil-moisture forecast (US-34)

- What: the Live forecast line says when the soil is drying out or getting wetter over the next
  5 days (Open-Meteo). Soil moisture was also tested as a risk-model input (ADR 0031).
- Why: the Live model lost its soil-moisture input in ADR 0021. This checks whether a daily
  source brings it back.
- Verify: `PYTHONPATH=src python -m pytest -q tests/test_soil_moisture.py`; in `web/`,
  `npm test`; for the experiment, `PYTHONPATH=src python scripts/soil_moisture_eval.py`.
- Result: no gain on the 2022 validation season and worse on 2024, so the model is unchanged.
- Out of scope: per-field soil moisture, and using it in the model.
