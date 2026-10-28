# 0020 — Prospective forecast log on a separate branch

Status: accepted (US-20, Issue #39). Replay results: [forecast_log.md](../forecast_log.md).

## Context
Historical test seasons were seen before the code was written. A forecast is only
convincing if it was published before the outcome was known, so that it can be checked later.

## Decision
- Each scheduled Pages run appends `latest.json["forecasts"]` to `forecasts.csv` on the
  orphan branch `forecast-log`. The run time goes in the `issued_at` column, and the Git commit time is
  a second public timestamp. `append_log` never overwrites a row (field, date, horizon), so a
  forecast can't be revised after the fact.
- Generated data stays off `main` (repository rule). Push runs don't write; only the schedule and manual runs do.
- `scoreboard()` scores a forecast only after `date + horizon` has passed and its outcome
  label (ADR 0010, same-date district peers) is in `outcomes.parquet`. Otherwise it counts as pending.
  It reports AUROC, red alarms that hit, red false alarms and missed onsets per horizon.
- The scoreboard is published as `live/scoreboard.json` and shown in Live mode.
- The spring scoring that fills `forecasts` and the live outcome labels are US-22 (Issue #46).
  Until then the log stays empty and the UI says forecasts start on 5 April.

## Consequences
- The workflow needs `contents: write`.
- `scripts/forecast_replay.py` runs a past season through the same code. On 2025 it gives
  exactly the offline AUROC, so the log and the scorer add no mistakes of their own.
