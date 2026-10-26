# 0006 — Regular 5-day grid with explicit observed masks

Status: Accepted (2026-10-26)

## Context

Sentinel-2 (cloud-dependent), Sentinel-1 (two orbit directions, ~6–12 day revisit) and daily
weather arrive at different, irregular times. Models need one time axis, and missing satellite
data must stay visible rather than be silently filled.

## Decision

- Grid dates t every 5 days from 1 April to 31 July (`PREDICTION_WINDOW`); a row summarises the
  half-open step (t − 5 d, t], so nothing after t enters row t.
- Satellite values: the latest qualifying observation inside the step (Sentinel-2 clear fraction
  ≥ 0.8; Sentinel-1 per orbit direction, columns suffixed `_asc` / `_desc`). No forward-fill: if
  nothing was observed the values are NaN, `*_observed` is false, and `*_days_since` gives the
  days since the latest observation on or before t (observations before 1 April count).
- Weather: per-step sums (`pr_mm`, `et0_mm`), means (`tas_c`, `hurs_pct`, `vpd_kpa`), extremes
  (`tasmin_c`, `tasmax_c`) and the last value (`soil_moist_pct`); a complete step has 5 days.
- Any imputation (forward-fill, interpolation) is a model-side choice that must use the masks.

## Consequences

- Soest 2024 sample: a step has a Sentinel-2 value 49% of the time, but some satellite value
  (S2 or either S1 orbit) 89% of the time.
- Masked sequence models (US-09) and tabular baselines (US-08) read the same table.
