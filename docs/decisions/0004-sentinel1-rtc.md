# 0004 — Sentinel-1: Planetary Computer RTC backscatter per field

Status: Accepted (2026-10-26)

## Context

Week-1 checks found a median longest gap of ~25 days between clear Sentinel-2 dates per field
(April–July). The 14- and 21-day horizons need a cloud-independent signal.

## Decision

- Source: Planetary Computer `sentinel-1-rtc` (IW GRD, radiometrically terrain corrected gamma0,
  linear power, 10 m, nodata −32768; CC BY 4.0). Terrain correction avoids having to run SNAP.
- Per field and acquisition: 10 m inward buffer, pixels valid in both VV and VH, median in linear
  power reported in dB (`vv_db`, `vh_db`) and `vh_vv_db = vh_db − vv_db`.
- `coverage` rule as for Sentinel-2: rows below 0.9 are dropped; overlapping slices of the same
  date and orbit direction keep the best-covered one.
- Ascending and descending passes are kept as separate rows (`orbit_state`, `relative_orbit`)
  because incidence angle and time of day (dew) shift backscatter; models must not mix them
  blindly.
- No speckle filter: the field median over hundreds of pixels already suppresses speckle.

## Consequences

- Sentinel-1B failed in December 2021, so 2022–2024 have only Sentinel-1A (lower revisit than
  2019–2021); Sentinel-1C data starts in 2025. Revisit density therefore differs by season and the
  observed mask must carry it.
