# Week 16 — Season greenness chart (US-30)

- What: each Live card shows the field's NDVI on clear images since 1 October against the median
  of its district peers, with a plain-words summary that is also the chart's accessible name and
  is read aloud (ADR 0027).
- Why: the winter hint ("behind the neighbours") now shows the data behind it, without reading.
- Verify: `PYTHONPATH=src python -m pytest -q tests/test_live.py`; in `web/`, `npm test`; a local
  `scripts/live_update.py --n 10` run writes `season` into the JSON.
- Out of scope: marking risk-level changes (needs the forecast log), satellite photos.
