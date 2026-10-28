# Week 18 — Nearby growth stage (US-32)

- What: each Live card says what stage winter wheat has reached around the field, from DWD's
  phenology observers within 40 km, with how many observers agree (ADR 0029).
- Why: the satellite lines are easier to read when you know whether the crop has just come up
  or is heading.
- Verify: `PYTHONPATH=src python -m pytest -q tests/test_phenology.py`; in `web/`, `npm test`.
  For real data: `cropews.data.phenology.fetch()` then `nearby_stage(obs, stations, 51.57, 8.1, date.today())`.
- Out of scope: a per-field stage model, using the stage as a model input.
