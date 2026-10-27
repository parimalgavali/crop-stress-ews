# 0011 — Sequence models: GRU-D and LSTM on windows of the 5-day grid

Status: Accepted (2026-10-27). Uses the protocol of [0008](0008-evaluation-protocol.md) and the
label of [0010](0010-peer-reference-label.md).

## Context

US-09 compares deep sequence models with the US-08 baselines. Satellite channels are irregularly
observed (clouds, orbit gaps), and the grid never forward-fills them (ADR 0006).

## Decision

- **Inputs per 5-day step:** day of year; S2 NDVI, NDMI, NDRE, EVI, MSI and the NDVI/NDMI/NDRE
  departure from the same-date district median (≥ 8 peers, the label's reference); S1 VV, VH, VH/VV
  per orbit direction; DWD precipitation, temperatures, humidity, VPD, ET0, soil moisture.
  Standardised with training-season mean/SD; missing → 0 (= training mean) plus an observed mask
  and days since the channel was last observed.
- **Causality:** the prediction at step t sees only a window of steps ending at t (left-padded),
  so no input after t is visible.
- **Models:** GRU-D (input decay to the mean, hidden-state decay with the gap; Che et al. 2018) and
  an LSTM on [value, mask, gap]. 32 hidden units, one multi-task head for 7/14/21 d, masked
  class-balanced BCE, Adam, early stopping on validation loss, 3-seed ensemble.
- **Selection and reporting:** the configuration (architecture × window × channel ablation) is
  chosen on validation AUROC only. Scores are Platt-calibrated on validation and thresholds
  frozen at 90% validation specificity; test is reported for every configuration for
  transparency, but only the validation-selected one is the headline.
- `torch` is an optional `seq` extra; CI installs the CPU wheel.

## Consequences

- Ablations are compared on validation; test numbers per ablation are descriptive only.
- With 40 Soest fields per season CIs are ±0.15–0.2; the six-district run is the decisive one.
