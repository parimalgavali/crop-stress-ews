# 0001 — Region NRW, crop winter wheat, seasons 2019–2025

Status: Accepted (2026-10-26)

## Context

The project is a job signal for German AgriTech/applied-AI employers. Employers cluster in NRW
(Rhineland: xarvio/BASF Köln, Bayer Monheim) and the adjacent Agrotech Valley (Osnabrück/OWL:
CLAAS and machinery makers). Berlin has the most startups but fewer agriculture-specific employers.

## Decision

- **Region:** NRW. Core districts by wheat area: Soest, Warendorf, Höxter, Coesfeld, Düren,
  Rhein-Erft-Kreis.
- **Crop:** winter wheat. Largest German crop (2.78 M ha in 2025) and the only one with field crop
  maps, field-level yield (YieldSAT: 188 German wheat fields), district yields and DWD phenology.
- **Seasons:** 2019–2025 (limited by public NRW parcel data). Predictions 1 April – 31 July.
- **Splits:** train 2019–2021 + 2023, validate 2022, test 2024, extra check 2025.

## Why 2024 is the test season

NRW winter-wheat yield: 2020 8.66, 2021 7.93, 2022 ~8.9, 2023 8.22, 2024 7.02, 2025 ~9.0 t/ha.
2022 was a good wheat year (the drought hit summer crops), so it cannot be the stress test season.
2024 was a wet year with yield 15% below the 2018–2023 average.

## Alternatives considered

Brandenburg (2010–2025 history, drier) — rejected as far from target employers. Silage maize —
no German field-level yield in YieldSAT; kept as a possible second crop.
