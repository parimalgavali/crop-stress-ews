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
- **Scope:** six core districts (Soest, Warendorf, Höxter, Coesfeld, Düren, Rhein-Erft-Kreis),
  30–40 sampled fields ≥ 2 ha per district and season; 190 test field-seasons.

## Label
A field is "behind its neighbours" when its NDVI or NDMI is at least 1.5 SD below the same-date
district median on two consecutive clear observations (the SD is fitted on training seasons only).
Onsets are counted until 30 June. Sanity check against district yields (42 district-seasons):
within-season ρ −0.28 (p 0.07) ([labels.md](labels.md)).

## Metrics — test 2024, six districts (190 field-seasons)
| Horizon | AUROC [95% CI] | Persistence AUROC | Sensitivity @ 90% spec | False alarms / 100 fields |
|---|---|---|---|---|
| 7 d | 0.742 [0.653–0.834] | 0.718 | 0.32 | 35 |
| 14 d | 0.795 [0.723–0.864] | 0.722 | 0.31 | 39 |
| 21 d | 0.768 [0.683–0.846] | 0.704 | 0.36 | 71 |

Red alarms preceded 21 of 29 onsets (72%), by a median of 15 days (range 5–20)
([error_analysis.md](error_analysis.md)).

## Intended use and limits
- **Intended use:** a portfolio demonstration of leakage-free early warning. It is **not** agronomic
  advice and has not been validated with farmers or field scouting.
- **What the label measures:** the label is relative to neighbouring fields. A stress that hits
  all fields in a district equally is invisible by design.
- **Sample size:** 190 test fields, 3.8–5.9% positive rows. The CIs narrowed (±0.07–0.09) but
  still overlap persistence at every horizon, so the gain over persistence is not proven.
- **Districts differ:** Düren had no onsets in 2024; Coesfeld has the most false alarms
  ([error_analysis.md](error_analysis.md)).
- **Weak spots:** reliability drops during long optical cloud gaps. Fields under 2 ha are absent
  from the sample.
- **Licences:** data licences in [ADR 0002](decisions/0002-data-sources.md). UFZ drought-monitor
  data is not used.
