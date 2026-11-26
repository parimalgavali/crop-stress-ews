# Case study: crop-stress early warning for winter wheat in NRW

One page for reviewers. Every number links to the doc it comes from.

## Problem
A farmer or adviser cannot walk every field. Satellite-observed changes may help prioritise
visits, but they do not establish a stress cause or a harvest loss. **Question:** for each field and date, will it start falling behind its district
neighbours within 7, 14 or 21 days? The answer has to be usable by someone who can't read a chart.

## Data (all free and open)
Europe-LAND/IACS parcels 2019–2025 and the weekly LWK parcel file, Sentinel-2 optical data,
Sentinel-1 radar, DWD HYRAS/AMBAV weather and the DWD ICON forecast. Six core districts, ~190
monitored winter-wheat fields per historical season.

## Method
- **Label:** the first label ("below the multi-year norm") tracked dry springs, not yield loss.
  It was replaced by a same-date district-peer label ([ADR 0010](decisions/0010-peer-reference-label.md),
  [label sanity](label_sanity.md)).
- **No leakage:** splits by season (train 2019–21 + 2023, validation 2022, test 2024 = wet year,
  extra check 2025). Nothing is fitted on the test season ([ADR 0008](decisions/0008-evaluation-protocol.md)).
- **Missing data:** satellite values are never forward-filled; every input has an observed mask
  and a days-since value.
- **Models:** persistence, logistic regression, LightGBM, GRU-D/LSTM. The served model is the
  calibrated logistic model for simple, model-specific explanations
  ([ADR 0012](decisions/0012-api-and-demo-model.md)).

## Results (test season 2024, held out)
| Horizon | AUROC [95% CI] | Persistence |
|---|---|---|
| 7 d | 0.74 [0.65–0.83] | 0.72 |
| 14 d | 0.80 [0.72–0.86] | 0.72 |
| 21 d | 0.77 [0.68–0.85] | 0.70 |

- Red alarms warned 21 of 31 canopy events (68%), a median of **13 days** ahead, with about
  3.7 repeated alerts per warned event. Only alarms whose own window contains the onset count
  ([ADR 0050](decisions/0050-horizon-aware-lead-time.md)).
- Corrected GRU-D results did not beat LightGBM on the validation gate; sequence models were
  not adopted ([ADR 0067](decisions/0067-grud-corrective-rerun.md)). Future challenger checks
  use paired field-bootstrap differences ([ADR 0054](decisions/0054-paired-comparison.md)).
- **Limits:** the label is relative to neighbouring fields, false alarms rise at 21 days, and Düren
  had no test onsets ([model card](model_card.md)).

## Historical replay versus Live
The 2024/2025 replay shows precomputed historical predictions. The separate Live view
shows periodically refreshed observations for season 2026/27; spring forecasts start on
5 April 2027 when eligible data and models are available. Neither is validated treatment advice.

## From a model to a running system (season 2026/27)
- **Live pipeline** on GitHub Actions every 5 days: current LWK parcels, Sentinel-1/2 and DWD data
  ([ADR 0015](decisions/0015-live-season.md)).
  - Health checks open and close a GitHub issue, and the site shows a stale-data notice
    ([ADR 0023](decisions/0023-pipeline-health.md)).
  - Model files are checked against pinned checksums.
- **Before farmers declare crops:** an in-season winter-wheat map from radar and optical data.
  Winter-cereal AUROC is 0.83–0.94 depending on the date. Telling wheat from barley is the weak
  spot after a wet autumn ([wheat map](winter_wheat_map.md)).
- **Winter cards:** emergence and waterlogging hints, validated on past winters and worded as hints
  ([winter checks](winter_checks.md)).
- **Spring risk from 5 April** with a live model that drops the monthly AMBAV inputs: at most
  −0.012 AUROC ([ADR 0021](decisions/0021-live-spring-risk.md)).
- **Forecasts are logged before outcomes are known** on a separate branch, then scored after 7/14/21
  days ([forecast log](forecast_log.md)). Opt-in ntfy alerts store no personal data
  ([ADR 0022](decisions/0022-alerts-ntfy.md)).
- **UI:** one screen, colour plus symbol plus word, EN/DE read-aloud, "check my field" in the
  browser, installable and offline ([ADR 0013](decisions/0013-one-screen-ui.md),
  [ADR 0017](decisions/0017-check-my-field.md), [ADR 0024](decisions/0024-installable-offline.md)).

## Ideas tested and rejected
- **The weather forecast as a model input:** even a perfect forecast added nothing on 2022, so it
  only appears on the cards ([weather forecast](weather_forecast.md)).
- **District harvest outlook:** the canopy signals were worse than "a normal year" on IT.NRW yields
  2019–2025, with an average error of 11–13% against 8%
  ([Issue #58](https://github.com/parimalgavali/crop-stress-ews/issues/58)).
- **Waterlogging as a field-level spring predictor:** it detects wet winters (124 against 28 of
  240 fields) but not which field will suffer ([winter checks](winter_checks.md)).

## Next
- Score spring 2027 from the forecast log, which is the true out-of-sample test.
- Add harvest-2026 labels from the LWK declarations and run the yearly champion/challenger retrain.
