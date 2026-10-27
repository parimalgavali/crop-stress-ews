# Baselines and evaluation protocol (US-08)

Protocol: [ADR 0008](decisions/0008-evaluation-protocol.md). Code: `src/cropews/features.py`,
`src/cropews/baselines.py`, `src/cropews/evaluation.py`, `scripts/train_baselines.py`.

## Features (all past-only, tested for look-ahead)

Last observed value, slope between the two latest observations and 15-day mean for NDVI, NDMI,
NDRE and Sentinel-1 VH / VH−VV (ascending and descending); NDVI/NDMI/NDRE anomaly against the
district median on the same date; days since the last S2 / S1 observation; 30-day water balance
(precipitation − ET0), hot steps (Tmax ≥ 30 °C) in 30 days, 15-day VPD, soil moisture, growing
degree days since 1 April, day of year.

## First result: Soest, 40 fields per season (2026-10-27)

Train 2019–2021 + 2023 (159 field-seasons), thresholds frozen at 90% specificity on 2022, test
2024 (40 fields). Test AUROC with 95% field-bootstrap CI; AUPRC with prevalence; FA = false
alarms per 100 field-seasons at the frozen threshold.

| Horizon | Model | AUROC [95% CI] | AUPRC (prev.) | Sensitivity | FA/100 |
|---|---|---|---|---|---|
| 7 d | persistence | 0.785 [0.594–0.918] | 0.198 (0.056) | 0.39 | 58 |
| 7 d | weather rule | 0.541 [0.461–0.623] | 0.064 | 0.00 | 0 |
| 7 d | logistic | 0.734 [0.568–0.887] | 0.266 | 0.56 | 100 |
| 7 d | LightGBM | 0.711 [0.594–0.876] | 0.309 | 0.44 | 55 |
| 14 d | persistence | 0.777 [0.641–0.883] | 0.207 (0.075) | 0.26 | 78 |
| 14 d | weather rule | 0.559 [0.492–0.621] | 0.100 | 0.00 | 0 |
| 14 d | logistic | 0.797 [0.647–0.894] | 0.203 | 0.71 | 198 |
| 14 d | LightGBM | 0.756 [0.637–0.882] | 0.347 | 0.29 | 42 |
| 21 d | persistence | 0.745 [0.618–0.863] | 0.217 (0.093) | 0.22 | 72 |
| 21 d | weather rule | 0.510 [0.428–0.591] | 0.102 | 0.00 | 0 |
| 21 d | logistic | 0.804 [0.612–0.929] | 0.365 | 0.67 | 138 |
| 21 d | LightGBM | 0.709 [0.566–0.847] | 0.285 | 0.16 | 30 |

## Reading

- **Gate not met.** LightGBM does not beat persistence on AUROC (CIs overlap at every horizon),
  although it has the best AUPRC at 7 and 14 days with fewer false alarms. Per ADR 0008 the label
  is revisited before US-09.
- **Persistence is strong because the label is an NDVI/NDMI anomaly:** fields already drifting
  below their district peers are the ones that cross −1.5 SD next. That makes the target partly
  "continue the trend", which is what this gate exists to catch.
- **Weather alone carries almost no signal** for this optical label (AUROC ≈ 0.5–0.56); the
  weather rule never alarms at the validation threshold.
- **Sample size dominates:** 40 test fields, 22–37 positive rows per horizon; CIs span ±0.15.
  The other five core districts (Sentinel-2 done, Sentinel-1 in progress) will be added.

## Next

- Label revision candidates (new ADR): require the anomaly relative to the field's own recent
  trajectory (onset = change, not level), or exclude rows whose current peer anomaly is already
  below −1 SD so the task is "new" stress only.
- Re-run with all six core districts once Sentinel-1 extraction finishes.

## Revised label (ADR 0010, same-date peers): Soest, test 2024 (2026-10-27)

Label chosen on 2019–2023 only (ADR 0010), then this single test run. Same protocol and features.

| Horizon | Model | AUROC [95% CI] | AUPRC (prev.) | Sensitivity | FA/100 |
|---|---|---|---|---|---|
| 7 d | persistence | 0.664 [0.490–0.866] | 0.130 (0.039) | 0.42 | 85 |
| 7 d | weather rule | 0.542 [0.434–0.695] | 0.046 | 0.00 | 0 |
| 7 d | logistic | 0.795 [0.635–0.937] | 0.223 | 0.17 | 25 |
| 7 d | LightGBM | 0.800 [0.618–0.948] | 0.196 | 0.33 | 45 |
| 14 d | persistence | 0.698 [0.537–0.863] | 0.159 (0.059) | 0.42 | 138 |
| 14 d | weather rule | 0.510 [0.367–0.645] | 0.065 | 0.00 | 0 |
| 14 d | logistic | 0.777 [0.623–0.905] | 0.211 | 0.31 | 62 |
| 14 d | LightGBM | 0.715 [0.533–0.922] | 0.231 | 0.31 | 28 |
| 21 d | persistence | 0.686 [0.544–0.827] | 0.163 (0.072) | 0.35 | 135 |
| 21 d | weather rule | 0.453 [0.306–0.596] | 0.071 | 0.00 | 0 |
| 21 d | logistic | 0.735 [0.530–0.898] | 0.213 | 0.47 | 132 |
| 21 d | LightGBM | 0.659 [0.446–0.896] | 0.267 | 0.29 | 30 |

- Persistence is no longer the model to beat: learned models lead at 7 d (LightGBM 0.80 vs 0.66)
  and logistic regression leads at 14/21 d, with fewer false alarms per 100 fields than persistence.
- **Gate (beyond CI overlap) still not met on test**, because 40 test fields give only 16–25
  positive rows per horizon and CIs of ±0.15–0.2. On validation (2022) LightGBM beats persistence
  by 0.15–0.20 AUROC at 7/14 d. The multi-district rerun (6 × 30 fields, Sentinel-1 extraction
  running) is the fix; no further label tuning on the test season.

## Six districts, test 2024 (2026-10-27)

Same label (ADR 0010), features and protocol; 190 field-seasons per season (756 train), no
retuning. Positive rows: 3.8% (7 d), 4.9% (14 d), 5.9% (21 d).

| Horizon | Model | AUROC [95% CI] | AUPRC | Sensitivity | FA/100 |
|---|---|---|---|---|---|
| 7 d | persistence | 0.718 [0.616–0.812] | 0.107 | 0.39 | 46 |
| 7 d | weather rule | 0.531 [0.459–0.607] | 0.039 | 0.00 | 0 |
| 7 d | logistic | 0.742 [0.653–0.834] | 0.103 | 0.32 | 35 |
| 7 d | LightGBM | 0.761 [0.692–0.829] | 0.097 | 0.34 | 63 |
| 14 d | persistence | 0.722 [0.631–0.813] | 0.129 | 0.40 | 79 |
| 14 d | weather rule | 0.457 [0.382–0.530] | 0.043 | 0.00 | 0 |
| 14 d | logistic | 0.795 [0.723–0.864] | 0.177 | 0.31 | 39 |
| 14 d | LightGBM | 0.792 [0.738–0.851] | 0.149 | 0.35 | 66 |
| 21 d | persistence | 0.704 [0.611–0.790] | 0.135 | 0.34 | 89 |
| 21 d | weather rule | 0.428 [0.357–0.502] | 0.050 | 0.00 | 0 |
| 21 d | logistic | 0.768 [0.683–0.846] | 0.180 | 0.36 | 71 |
| 21 d | LightGBM | 0.737 [0.668–0.810] | 0.150 | 0.30 | 83 |

- CIs are about half as wide as on Soest alone (±0.07–0.09).
- Logistic regression and LightGBM beat persistence on every point estimate, with fewer false
  alarms at 14/21 d (logistic). The **ADR 0008 gate (non-overlapping CIs) is still not met**:
  e.g. 14 d logistic [0.723–0.864] vs persistence [0.631–0.813].
- The weather-only rule stays at chance.
