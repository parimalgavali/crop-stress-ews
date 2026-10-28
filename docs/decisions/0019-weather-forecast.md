# 0019 — 5-day DWD ICON forecast: shown on Live cards, not a model input

Status: accepted (US-19, Issue #38). Results: [weather_forecast.md](../weather_forecast.md).

## Context
Warnings should mention the coming weather ("heavy rain coming"). Evaluating a forecast as a
model input needs forecasts as they were issued at the time; using observed future weather
would leak. Archived DWD ICON runs with lead time (Open-Meteo Previous Runs API) exist only
from February 2024, so the training years 2019–2023 have none.

## Decision
- **Source:** DWD ICON (`icon_seamless`) via Open-Meteo, CC BY 4.0, JSON with CORS. Raw DWD
  MOSMIX/ICON files (GRIB/KMZ, ~80 MB per run) would need a decoder in CI for the same data.
- **Display:** `live_update.py` fetches the 5-day forecast at each district's field centroid
  and adds `forecast[district]` (rain sum, lowest minimum, frost nights) to `latest.json`.
  The card says e.g. "Next 5 days (weather forecast): 24 mm rain, lowest −2 °C · heavy rain
  expected · frost on 1 night" (EN/DE, read aloud). ≥ 20 mm counts as heavy rain. If the
  service fails, the line is left out.
- **Model input — evaluated, not adopted:** `scripts/forecast_eval.py` trains with observed
  next-5-day weather (a perfect forecast, upper bound) on the training years, compares on
  2022, then scores 2024/2025 with the archived ICON forecast as known on each date. On 2022
  the forecast adds nothing (AUROC change −0.01 to 0.00 for the six model/horizon pairs), so
  under the protocol (choose on validation only) the risk model stays unchanged.

## Consequences
- The forecast is context for the user, not part of the risk score.
- ICON skill over 5 days at district scale (2024–25, Apr–Jul): rain correlation 0.61, MAE
  6 mm; it caught 48 % of the ≥ 20 mm periods and half of its ≥ 20 mm forecasts didn't happen.
  The card therefore says "expected", not a warning.
- Re-run the evaluation once spring 2026 adds a third archived season.
- Check my field (US-17, PR #43) can fetch the same forecast in the browser later.
