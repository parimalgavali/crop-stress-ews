# 5-day weather forecast: evaluation (US-19, ADR 0019)

Archived DWD ICON forecasts (Open-Meteo Previous Runs API) at the 6 district centroids,
spring 2024 and 2025, issue dates 1 April – 31 July. Reproduce with
`scripts/forecast_eval.py` after saving the archive to `data/interim/forecast/`
(`cropews.data.forecast.archived_forecast`).

## Forecast skill vs HYRAS (next 5 days, 1,404 district issue dates)

| Rain correlation | Rain MAE | Lowest-temperature MAE | ≥ 20 mm periods caught | ≥ 20 mm forecasts that didn't happen |
|---|---|---|---|---|
| 0.61 | 6.1 mm | 1.4 °C | 48 % | 51 % |

## Does the forecast help the risk model? (AUROC)

Validation 2022 uses the perfect forecast (observed weather). Test 2024 and 2025 use the
archived ICON forecast as known on each date.

| Horizon | Model | 2022 without / with | 2024 without / with ICON (perfect) | 2025 without / with ICON |
|---|---|---|---|---|
| 7 d | logistic | 0.858 / 0.857 | 0.742 / 0.746 (0.747) | 0.868 / 0.879 |
| 7 d | LightGBM | 0.878 / 0.877 | 0.761 / 0.801 (0.785) | 0.846 / 0.870 |
| 14 d | logistic | 0.784 / 0.784 | 0.795 / 0.801 (0.797) | 0.879 / 0.892 |
| 14 d | LightGBM | 0.833 / 0.823 | 0.792 / 0.811 (0.794) | 0.860 / 0.860 |
| 21 d | logistic | 0.758 / 0.758 | 0.768 / 0.769 (0.768) | 0.868 / 0.871 |
| 21 d | LightGBM | 0.823 / 0.819 | 0.737 / 0.745 (0.739) | 0.823 / 0.813 |

## Reading
- On the validation season the forecast adds nothing, so it is not added to the risk model.
- The small 2024/2025 gains are not evidence. The real ICON forecast beat the perfect forecast
  in 2024 for LightGBM, which can only be noise; the bootstrap intervals (±0.03–0.04) overlap.
- Likely reason: the stress label compares a field with its district peers, and a district-wide
  forecast is the same for every peer.
- Useful for users anyway: rain and frost in the next days affect field work and spraying.
