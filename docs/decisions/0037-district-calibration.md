# ADR 0037: Per-district calibration tested and rejected

Status: Rejected (open question from ADR 0021 follow-up, Issue #87)

## Context
The served model is Platt-scaled and thresholded on the pooled 2022 validation season
(ADR 0021). Coesfeld showed many false alarms, so per-district calibration was a
candidate fix.

## Test
`scripts/district_calibration_eval.py`: inside 2022 validation, 5-fold over fields —
Platt scaling and red/amber thresholds (90 %/75 % specificity) fitted either pooled or
per district on the calibration folds, evaluated out-of-fold (190 fields, ~30/district).

## Result
Per-district calibration does not reduce false alarms overall; it moves them between
districts. Coesfeld red-alarm burden (false alarms per 100 fields): 127→110 (21 d),
127→110 (14 d); but Soest worsens 70→112 (21 d) and total burden is unchanged
(≈113/100 both ways). Sensitivity shifts a little at random.
The false-alarm problem is not district bias in the probability scale — the Coesfeld
signal itself is less separable — so pooled calibration stays.

## Consequences
- `live_model` keeps pooled Platt + thresholds (ADR 0021).
- Coesfeld false alarms remain a known limitation (see `docs/project_memory.md`).
