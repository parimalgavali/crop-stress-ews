# 0008 — Evaluation protocol and baselines

Status: Accepted (2026-10-27)

## Decision

- Splits by season (ADR 0001): train 2019–2021 + 2023, validation 2022, test 2024, extra check 2025.
  The protocol is fixed before any sequence model is trained (US-09).
- Rows: every 5-day grid row with a non-NaN `onset_{h}d` target (ADR 0007); features use only rows
  at or before t (`cropews.features`, tested for look-ahead).
- Alarm threshold per model and horizon at 90% specificity on the validation season, then frozen.
- Test metrics per horizon: AUROC, AUPRC (with prevalence), sensitivity and specificity at the
  frozen threshold, false alarms per 100 field-seasons, Brier score for probabilistic models.
  95% CIs by bootstrapping whole fields (rows of one field are correlated).
- Baselines: persistence (current NDVI/NDMI peer anomaly continues), weather-only rule (30-day
  water deficit + heat), logistic regression (median impute + missing indicators), LightGBM.
- Gate: LightGBM must beat persistence on test AUROC beyond the CI overlap; otherwise the label
  (ADR 0007) is revisited before US-09.

## Why

Season splits keep the wet 2024 season unseen; validation-frozen thresholds prevent tuning on
test; alarm burden per field is what users of an early-warning system feel.

## Consequences

Spatial blocking inside the training seasons (grouping by district) is used only for
hyperparameter checks; with few districts per season, CIs are wide and reported as such.
