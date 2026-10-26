# 0007 — Stress-onset label: Sentinel-2 anomaly against a training-only baseline

Status: Accepted (2026-10-26)

## Context

No field-level stress observations exist for NRW. The label must be computable for every field
and season, defined before modelling, and free of test-season leakage.

## Decision

See `docs/labels.md`. NDVI or NDMI z < −1.5 against a (district, 10-day bin) baseline fitted on
training seasons only, for ≥ 2 consecutive clear observations, onset on or before 30 June.
Targets `onset_{7,14,21}d` on the 5-day grid; missing when in an event, unobservable, or past the
cutoff.

## Consequences

- Threshold, bin width and cutoff are fixed now; changing them after seeing test results would
  be leakage. The validation season (2022) is where they may be tuned.
- The label must pass the US-07 sanity check (more events in 2024 and 2021 than in 2022/2025).
