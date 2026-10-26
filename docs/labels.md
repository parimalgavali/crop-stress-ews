# Stress-onset label

There is no field-level ground truth for crop stress in NRW, so the label is a **Sentinel-2
anomaly** defined before any model is trained (ADR 0007). Code: `src/cropews/labels.py`.

## Definition

1. **Clear observations:** Sentinel-2 rows with clear fraction ≥ 0.8 and both NDVI and NDMI.
2. **Baseline:** mean and SD of NDVI and NDMI per (district, 10-day day-of-year bin), fitted on
   training seasons **only** (2019–2021, 2023); bins with fewer than 20 observations are dropped.
   The same baseline is applied to validation (2022), test (2024) and 2025.
3. **Below:** a clear date where NDVI or NDMI is more than 1.5 SD under the baseline (z < −1.5).
4. **Event:** at least 2 consecutive below dates (consecutive clear observations of that field).
   Onset = first below date; it must be on or before 30 June (senescence and harvest change the
   canopy for reasons other than stress). Recovery = next clear date that is not below.
5. **Targets** for grid date t and horizon h ∈ {7, 14, 21}: `onset_{h}d` = 1 if an onset falls in
   (t, t + h], else 0. Set to missing when
   - the field is in an event at t (onset ≤ t < recovery) — already-stressed fields are not
     "early" warnings;
   - there is no clear observation in (t, t + h] — the label cannot be confirmed or ruled out;
   - t + h is after 30 June.

## Limitations

- An optical anomaly is a proxy: it can come from late sowing, lodging, hail, cultivar or
  management, not only water or disease stress. US-07 checks it against district yields.
- Cloudy periods delay detection; the onset date is the first *observed* below date.
- In-event exclusion uses the recovery date, which is in the future at t. This only filters
  training/evaluation rows; a deployed model must use current z-scores as features instead.
- One district baseline per bin ignores within-district soil differences.
