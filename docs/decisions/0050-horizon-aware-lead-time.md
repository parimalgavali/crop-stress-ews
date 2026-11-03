# ADR 0050: Lead time counts only alarms whose own window contains the onset

- Status: accepted, 2026-10-26
- Context: Review finding 4.2 — `lead_times` credited any red alarm within 21 days before onset,
  ignoring `horizon_days`; it also used the first grid `in_event` date (not the recorded onset) and
  reported only the first event per field-season.
- Decision: an alarm hits an event iff `origin < onset <= origin + horizon_days`. Events come from
  the exact `events_*.parquet` tables (fallback: contiguous `in_event` runs). All events per
  field-season are reported; events starting on/before the first predict date are excluded. Output
  adds `n_alarms` (repeated-alert burden) and missed events.
- Recomputed claims (2024, red, all horizons): 21 of 31 events warned (was "21 of 29"), median
  lead 13 days (was "15"), mean 11.5, ~3.7 repeated alerts per warned event. Any older wording
  ("21 of 29, median 15 days") is superseded.
