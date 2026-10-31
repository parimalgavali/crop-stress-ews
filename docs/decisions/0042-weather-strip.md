# ADR 0042: Daily forecast behind the weather strip on Live cards

Status: Accepted (US-45, Issue #97)

## Context
Farmonaut and xarvio lead with a compact per-field weather chart. Our card only
spoke the 5-day aggregates ("X mm rain, lowest Y °C"); the daily shape — which
day it rains, how cold which night is — was invisible.

## Decision
- `forecast_summary` additionally writes `fc_days`: the 5 daily records
  (date, pr mm, tmin, tmax) behind the existing aggregates. +0.5 KB per district.
- The card renders a minimal strip: weekday, rain bar (scaled to 5 mm),
  and "low°/high°". The whole strip is one `role="img"` element with a spoken
  label, matching the season chart's pattern.
- Display only: `fc_days` is not a model input (same rule as ADR 0019 — weather
  never enters the model).

## Consequences
- Payload stays small: only 6 districts × 5 days.
- Archived forecasts (no `tasmax_c`) fall back to `tasmin_c` for `tmax`.
