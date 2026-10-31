# Week 31 — Weather strip on Live cards (US-45)

- What: per-field card shows the 5-day ICON forecast as weekday rain bars and
  low/high temperatures; one spoken aria-label, EN/DE.
- Backend: `forecast_summary` emits `fc_days` alongside the aggregates.
- Verify: `pytest tests/test_forecast.py`; typecheck + e2e incl. axe pass.
