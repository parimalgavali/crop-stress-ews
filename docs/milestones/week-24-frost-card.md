# Week 24 — Winter frost card (US-38)

- What: the forecast line now says whether expected frost sits on bare ground or under
  protective snow, flagging "hard frost on bare ground" below −8 °C.
- Why: the site should stay useful in winter; frost nights alone over-warn.
- Verify: `pytest tests/test_forecast.py`, `vitest run src/live.test.ts` (snow/bare cases).
- Out of scope: frost as a model input (no validated winter label); exact agronomic
  thresholds.
