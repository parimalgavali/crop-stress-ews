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
