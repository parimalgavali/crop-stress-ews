# 0021 — Live spring risk from 5 April without AMBAV features

Status: accepted (US-22, Issue #46).

## Context
The demo model (ADR 0012) uses ET0 and soil moisture from DWD AMBAV. AMBAV is published
monthly, so these values are missing in a live run.

## Decision
- `scripts/export_live_model.py` fits the same recipe without `water_balance_30d` and
  `soil_moist_pct`: US-08 logistic per horizon, Platt calibration on 2022, red/amber at 90 %/75 %
  validation specificity. Saved as `risk_live.joblib`, published as the pre-release `risk-v1`, not committed.
- Cost of dropping them (AUROC, full → live):

  | Horizon | 2022 validation | 2024 test | 2025 check |
  |---|---|---|---|
  | 7 d | 0.858 → 0.858 | 0.742 → 0.731 | 0.868 → 0.873 |
  | 14 d | 0.784 → 0.778 | 0.795 → 0.783 | 0.879 → 0.886 |
  | 21 d | 0.758 → 0.755 | 0.768 → 0.760 | 0.868 → 0.875 |

- From 5 April to 31 July, `live_update.py --risk-model` builds the 5-day grid from 1 April for the
  parcels in `spring_monitoring` (US-18), or all sampled parcels if there is no crop map. It
  scores the latest grid step on or before the run date and writes `risk[field_id]` (the same
  shape as the replay risk cards, with reasons) and `forecasts` rows for the forecast log (ADR 0020).
- The Live card shows the three risk cards above the conditions.

## Consequences
- Live forecasts are real forecasts only once the run date is in the future of the data.
  `score_live` uses only grid steps ≤ the run date (tested).
- Live outcome labels for the scoreboard need the peer-relative labels on live parcels. That
  comes once enough of spring 2027 has been observed (follow-up in Issue #39).
