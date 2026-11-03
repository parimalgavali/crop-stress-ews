# ADR 0053: Check-my-field comparison needs a ≥20-day-old scene

- Status: accepted, 2026-10-26
- Context: Review finding 4.5 — `optical` in web/src/checkField.ts skipped any candidate more than
  20 days older than the latest clear scene (strict `< -20`), while the diff requires a gap ≥ 20
  days; only an exactly-20-day gap worked.
- Decision: skip candidates whose age gap vs the latest scene is *below* `CHANGE_MIN_GAP_DAYS`.
  `optical` is now exported with injectable deps so the whole selection flow (search → token →
  SCL clear-check → band read → NDVI diff) is vitest-covered with mocked IO.
- Verified: 15-day-only → `ndvi_change: null`; 15-day skipped + 25-day → change reported.
