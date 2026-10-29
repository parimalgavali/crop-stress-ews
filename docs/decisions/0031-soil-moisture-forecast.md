# ADR 0031: Soil-moisture trend from Open-Meteo on the forecast line, tested as a model input

Status: Accepted (US-34, Issue #75)

## Context
The Live risk model dropped DWD AMBAV soil moisture because it is published monthly (ADR 0021).
Open-Meteo (CC BY 4.0) gives daily volumetric soil moisture at 0–7 and 7–28 cm, both as a
forecast and, for 2019–2025, as ERA5 reanalysis in its archive. Past soil-moisture forecasts
are not archived for the training years.

## Decision
- Live: at each district's field centroid (the same point as the weather forecast, ADR 0019),
  `fc_sm_change_5d` is the 7–28 cm moisture averaged over the next 5 days, minus today's value.
  The forecast line adds "soil drying out" at ≤ −0.02 m³/m³ or "soil getting wetter" at ≥ +0.02,
  in EN/DE and read aloud.
  - In ERA5 April–June 2019–2025 these thresholds are about the 10th and 90th percentiles, so the
    note shows on clearly unusual days only.
  - If the service fails, the note is left out.
- Model input experiment (`scripts/soil_moisture_eval.py`): Live features (ADR 0021) plus ERA5
  `sm_top`, `sm_root`, and `sm_root_change_5d` as a perfect 5-day forecast, at district
  centroids. Logistic model, AUROC:

| Horizon | Variant | 2022 validation | 2024 test | 2025 check |
|---|---|---|---|---|
| 7 d | Live | 0.858 | 0.731 | 0.873 |
| 7 d | + soil moisture now | 0.857 | 0.722 | 0.893 |
| 7 d | + now + 5-day change | 0.857 | 0.723 | 0.891 |
| 14 d | Live | 0.778 | 0.783 | 0.886 |
| 14 d | + now + 5-day change | 0.777 | 0.756 | 0.902 |
| 21 d | Live | 0.755 | 0.760 | 0.875 |
| 21 d | + now + 5-day change | 0.756 | 0.723 | 0.886 |

- **Not adopted.** There is no change on 2022 (±0.001). 2024 gets worse by 0.01–0.04 and 2025
  better by 0.01–0.02. As with the weather forecast (ADR 0019), the label compares each field
  with its district neighbours, and they all get the same district value.
- ERA5 and the forecast model's soil moisture are different products, which is another reason
  not to train on one and serve the other.

## Consequences
- Each run makes one more request per district (6 in total).
- The line is context only. It does not change the traffic lights.
