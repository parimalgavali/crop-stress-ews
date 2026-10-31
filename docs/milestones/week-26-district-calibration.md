# Week 26 — Per-district calibration test (rejected)

- What: pooled vs per-district Platt/thresholds, 5-fold cross-fit inside 2022 validation
  (`scripts/district_calibration_eval.py`, report `outputs/district_calibration.json`).
- Result: no reduction in false alarms — they shift between districts. Pooled stays.
- Follows the ADR 0008 gate: adopt only if validation improves.
