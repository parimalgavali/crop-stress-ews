# In-season winter-wheat map: results (US-18, ADR 0018)

Population: 60 arable parcels per district and season (all crops, as in Live), 6 core districts.
Train 2020, 2021, 2023 (1,080 parcels); model choice on 2022 (360); held-out test 2024 (360);
extra check 2025 (360). Features: monthly Sentinel-1 and clear Sentinel-2 medians from October.
Metrics at p ≥ 0.5. Reproduce with `scripts/extract_s{1,2}.py --crops arable --window winter`
then `scripts/cropmap_train.py`.

## AUROC by cutoff

| Cutoff | Target | Model (chosen on 2022) | Validation 2022 | Test 2024 | Extra 2025 |
|---|---|---|---|---|---|
| 1 Dec | winter wheat | logistic | 0.83 | 0.75 | 0.88 |
| 1 Feb | winter wheat | LightGBM | 0.86 | 0.83 | 0.87 |
| 1 Apr | winter wheat | LightGBM | 0.93 | 0.86 | 0.92 |
| 1 Dec | any winter cereal | LightGBM | 0.86 | 0.83 | 0.84 |
| 1 Feb | any winter cereal | LightGBM | 0.92 | 0.89 | 0.89 |
| 1 Apr | any winter cereal | LightGBM | 0.97 | 0.92 | 0.94 |

Precision / recall / F1 over all districts, 1 Apr model: wheat 0.64 / 0.54 / 0.59 on 2024 and
0.66 / 0.91 / 0.77 on 2025; any winter cereal 0.86 / 0.82 / 0.84 on 2024 and 0.86 / 0.90 / 0.88
on 2025.

A single full-winter model is not usable before April: with later months missing it scored
almost every 2024 parcel below 0.5 (wheat recall 0.03 on 1 Dec). Hence one model per cutoff.

## Test 2024 per district (1 Apr model)

| District | Parcels | Wheat | Wheat precision | Wheat recall | Wheat F1 | Cereal F1 |
|---|---|---|---|---|---|---|
| Coesfeld | 60 | 17 | 0.58 | 0.65 | 0.61 | 0.75 |
| Düren | 60 | 24 | 0.75 | 0.50 | 0.60 | 0.89 |
| Höxter | 60 | 20 | 0.71 | 0.50 | 0.59 | 0.94 |
| Rhein-Erft-Kreis | 60 | 17 | 0.91 | 0.59 | 0.71 | 0.92 |
| Soest | 60 | 17 | 0.71 | 0.59 | 0.65 | 0.78 |
| Warendorf | 60 | 5 | 0.10 | 0.20 | 0.13 | 0.69 |
| All | 360 | 100 | 0.64 | 0.54 | 0.59 | 0.84 |

## What gets confused (test 2024, 1 Apr wheat model)

Flagged as wheat: 54 of 100 declared wheat, 10 of 22 triticale, 9 of 48 winter barley, 2 of 55
silage maize. The cereal model flags 46 of 48 barley, 18 of 22 triticale and 77 of 100 wheat.

## Reading

- Telling winter cereals from other crops works well (AUROC 0.92–0.94 by April).
- Telling wheat from barley and triticale is the hard part, and 2024 is worst: after the very
  wet autumn 2023 much wheat was sown late, so it looked like bare soil for most of the winter
  and half of it was missed. In the drier 2024/25 winter, recall was 0.91.
- Warendorf 2024 had only 5 wheat parcels in the sample, so its numbers are noise.
- For spring monitoring the wheat map is used as specified (p ≥ 0.5). Because recall can drop
  to about 0.5 in wet autumns, the forecast log (US-20) should also record the cereal map, and
  the set should be checked against the declarations when they are published in May.

## Live dry run (as of 5 December 2025, 1 Dec model)

`live_update.py --n 5 --as-of 2025-12-05 --cropmap models` on 30 current LWK parcels, whose
declarations (harvest 2026) are already published, so the guess can be checked: 12 parcels
entered `spring_monitoring`. 7 of them were declared winter wheat, 3 winter triticale and
2 potatoes. 7 of the 9 declared wheat parcels were included. All maize, beet and grass parcels
scored ≤ 0.07.
