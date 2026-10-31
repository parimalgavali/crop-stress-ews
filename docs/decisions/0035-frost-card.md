# ADR 0035: Winter frost card — hard frost vs. protective snow

Status: Accepted (US-38, Issue #83)

## Context
The forecast line already counted frost nights (US-19), but a −2 °C night under snow is
harmless while −10 °C on bare ground can damage even hardened winter wheat. The card gave
the same message for both.

## Decision
- `live_forecast` also fetches Open-Meteo `snowfall_sum` (same ICON model, same request);
  `forecast_summary` adds `fc_snow_5d_cm`.
- The frost note becomes one of three, in plain words: frost under expected snow
  ("snow expected — that protects the crop"), frost on bare ground, or — at
  `fc_tmin_5d_c <= -8 °C` without snow — "hard frost on bare ground — worth watching".
- −8 °C and 1 cm are display heuristics, not validated agronomic thresholds; the wording
  stays a hint ("worth watching"), not a diagnosis.
- Display context only, not a model input — same rule as the weather forecast (ADR 0019)
  and soil moisture (ADR 0031). Winter frost damage was not measured as a label.

## Consequences
- The site stays useful December–March, before spring risk starts on 5 April.
- Archived forecast data has no snowfall column; `forecast_summary` then reports 0 cm,
  which only affects offline experiments.
