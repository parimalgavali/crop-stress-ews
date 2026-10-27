# Model card — crop-stress early warning (demo model)

## Model
- **Task:** for an NRW winter-wheat field on a 5-day grid date, give the probability that a stress
  event starts within 7, 14 or 21 days ([ADR 0010](decisions/0010-peer-reference-label.md) label).
- **Served model:** logistic regression with one model per horizon, Platt-calibrated on the 2022
  validation season. Traffic-light thresholds are amber at 75% and red at 90% validation
  specificity ([ADR 0012](decisions/0012-api-and-demo-model.md)). Reasons are the model's own
  contributions (coefficient × standardised feature), grouped into plain-language EN/DE text.
- **Research models (not served):** LightGBM and the GRU-D/LSTM sequence models
  ([sequence_models.md](sequence_models.md)) perform on par with it. Their confidence intervals
  overlap.

## Data
- **Fields:** Europe-LAND / IACS NRW (crop code 115).
- **Satellite:** Sentinel-2 L2A indices, clear-pixel masked, no forward fill; Sentinel-1 RTC VV/VH,
  ascending and descending kept separate.
- **Weather:** DWD HYRAS and AMBAV.
- All inputs are aggregated to 5-day steps, 5 April – 31 July ([ADR 0002](decisions/0002-data-sources.md)).
- **Splits by season:** train 2019–21 and 2023, validation 2022, test 2024 (a wet, poor
  season), extra check 2025.
- **Current scope:** Soest only. The other five core districts are pending the Sentinel-1
  extraction.

## Label
A field is "behind its neighbours" when its NDVI or NDMI is at least 1.5 SD below the same-date
district median on two consecutive clear observations (the SD is fitted on training seasons only).
Onsets are counted until 30 June. Sanity check against district yields (42 district-seasons):
within-season ρ −0.28 (p 0.07) ([labels.md](labels.md)).

## Metrics — test 2024, Soest
| Horizon | AUROC [95% CI] | Sensitivity @ 90% spec | False alarms / 100 fields |
|---|---|---|---|
| 7 d | 0.795 [0.635–0.937] | 0.17 | 25 |
| 14 d | 0.777 [0.623–0.905] | 0.31 | 62 |
| 21 d | 0.735 [0.530–0.898] | 0.47 | 132 |

Red alarms preceded 6 of 9 onsets, by a median of 17.5 days ([error_analysis.md](error_analysis.md)).

## Intended use and limits
- **Intended use:** a portfolio demonstration of leakage-free early warning. It is **not** agronomic
  advice and has not been validated with farmers or field scouting.
- **What the label measures:** the label is relative to neighbouring fields. A stress that hits
  all fields in a district equally is invisible by design.
- **Sample size:** 40 test fields from one district. The confidence intervals are wide, and the
  model does not beat persistence beyond the CIs at 14/21 d.
- **Weak spots:** reliability drops during long optical cloud gaps. Fields under 2 ha are absent
  from the sample.
- **Licences:** data licences in [ADR 0002](decisions/0002-data-sources.md). UFZ drought-monitor
  data is not used.
