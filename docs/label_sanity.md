# Label sanity check against district yields (US-07)

Code: `src/cropews/data/yields.py`, `src/cropews/sanity.py`, `scripts/download_yields.py`,
`scripts/label_sanity.py`. Yields: IT.NRW Landesdatenbank table 41241-03i (winter wheat, t/ha,
dl-de/by-2-0). Yield anomaly = district yield / mean of the district's other years (2005–2025) − 1.

## Run (2026-10-27)

Six core districts, 30 sampled wheat fields per district-season (Soest 40), 2019–2025;
Coesfeld 2025 still downloading (41 of 42 district-seasons). Share of fields with ≥ 1 event:

| District | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Coesfeld | 0.20 | 0.30 | 0.10 | 0.33 | 0.20 | 0.43 | — |
| Düren | 0.03 | 0.20 | 0.10 | 0.20 | 0.10 | 0.17 | 0.23 |
| Höxter | 0.13 | 0.33 | 0.03 | 0.33 | 0.03 | 0.20 | 0.13 |
| Rhein-Erft-Kreis | 0.10 | 0.27 | 0.03 | 0.13 | 0.13 | 0.13 | 0.17 |
| Soest | 0.20 | 0.30 | 0.12 | 0.18 | 0.18 | 0.25 | 0.22 |
| Warendorf | 0.10 | 0.33 | 0.17 | 0.23 | 0.13 | **0.83** | 0.37 |
| **Mean share** | 0.13 | 0.29 | 0.09 | 0.24 | 0.13 | **0.34** | 0.23 |
| **Mean yield anomaly** | −3% | +8% | −8% | +5% | −2% | **−19%** | +7% |

Spearman ρ of event share vs yield anomaly (negative = label tracks yield loss):

| Comparison | ρ | p | n |
|---|---|---|---|
| All district-seasons | +0.18 | 0.27 | 41 |
| Within season (season means removed) | **−0.46** | **0.003** | 41 |
| All district-seasons without 2024 | +0.44 | 0.008 | 35 |

The map (`python scripts/label_sanity.py`, written to `data/outputs/label_sanity_map.png`, not
committed) shows the same pattern: 2024 dark in Warendorf and Coesfeld, 2020/2022 elevated
everywhere.

## Conclusion

- **Spatially the label works:** within a season, districts with more events lose more yield
  (ρ = −0.46). 2024 has the most events and the largest loss, and in 2024 the two worst districts
  by yield (Warendorf −29%, Coesfeld −26%) have the highest event shares.
- **Across seasons it does not:** the dry springs 2020 and 2022 produce many events but good
  yields, and the poor 2021 season has the fewest events. The label responds to early canopy
  anomalies that winter wheat recovers from, and misses late-season losses (2021: cool spring,
  wet July). The ADR 0007 expectation "more events in 2024 and 2021 than in 2022/2025" holds for
  2024 only.
- **Together with the US-08 gate** (LightGBM does not beat persistence), the label is revised
  before sequence models — [ADR 0009](decisions/0009-label-sanity-outcome.md).

Limitations: 30 fields per district-season is a small sample (±0.15 on a share); the yield
reference spans 2005–2025 and includes trend; district yields include all wheat, not the sample.
