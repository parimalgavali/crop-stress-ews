# Week 13 — Prospective forecast log (US-20)

- `cropews.forecast_log`: append-only log, outcome join, per-horizon scoreboard.
- Pages workflow writes `forecasts.csv` to the `forecast-log` branch and publishes `live/scoreboard.json`.
- Replay of 2025 reproduces the offline AUROC exactly ([forecast_log.md](../forecast_log.md), ADR 0020).
- Spring live scoring that fills the log: US-22 (Issue #46).
