# ADR 0026: Yearly champion/challenger retraining of the Live risk model

Status: Accepted (US-28, Issue #63)

## Context
A new labeled season arrives every year. Retraining blindly could make the live model worse
(see the 2025 backtest in `docs/retraining.md`). Changing the published model also changes the
forecasts in the forecast log (ADR 0020).

## Decision
- Retraining is a manual yearly routine (`scripts/retrain.py`), not a scheduled job. Building a
  season's labels needs hours of extraction, and a model change needs review.
- Gate: the challenger is scored against the published champion on a season neither has seen. It
  is promoted only on a mean AUROC gain with no horizon worse by more than 0.01.
- Calibration and thresholds stay on the 2022 validation season, so the meaning of red and amber is
  unchanged.
- Publishing a promoted model uses a new `risk-vN` release with `models.sha256`, and the models are
  swapped only between seasons (August–March), never during a spring that is being logged.

## Consequences
- The 2025 backtest keeps `risk-v1`.
- The test is a single holdout season, about 2,000 field-dates at 7 days, so small differences are
  within noise. The gate prefers keeping the champion.
