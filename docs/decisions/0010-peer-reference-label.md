# 0010 — Stress label against same-date district peers

Status: Accepted (2026-10-27). Amends [0007](0007-stress-label.md) (reference only); follows
[0009](0009-label-sanity-outcome.md).

## Context

The ADR 0007 label compares a field with a training-season climatology per (district, 10-day bin).
US-07 showed it tracks yield loss within seasons but is dominated by season-wide shifts (dry
springs 2020/2022), and US-08 showed LightGBM cannot beat persistence on it.

## Options compared (selection on 2019–2023 only; 2024/2025 not used)

Event share vs district yield anomaly, Spearman ρ over 2019–2023 district-seasons, and Soest
validation (2022) AUROC, persistence vs LightGBM:

| Reference | ρ all | ρ within season | 7 d persist / LGBM | 14 d | 21 d |
|---|---|---|---|---|---|
| climatology (ADR 0007) | +0.42 | −0.41 | 0.76 / 0.79 | 0.75 / 0.79 | 0.75 / 0.72 |
| **same-date peers** | **−0.09** | **−0.48** | **0.64 / 0.84** | **0.66 / 0.82** | 0.68 / 0.77 |
| climatology + below in June | +0.35 | −0.47 | 0.76 / 0.81 | 0.75 / 0.75 | 0.75 / 0.71 |
| peers + below in June | −0.09 | −0.51 | 0.58 / 0.77 | 0.59 / 0.74 | 0.63 / 0.68 |

Also tried: dropping rows whose current peer anomaly is already low ("fresh" onsets) — no
consistent gain, not adopted.

## Decision

A field is *below* on a clear date if its NDVI or NDMI departure from the **median of its district
peers on the same date** (≥ 8 clear peers) is more than 1.5 SD under zero, with the SD fitted per
(district, 10-day bin) on training seasons. Event rule, cutoff and targets are unchanged.
`scripts/build_labels.py --reference peer` is the default; `--reference climatology` keeps ADR 0007.

## Consequences

- The label means "this field is falling behind its neighbours", a field-level relative signal.
  Season-wide losses (e.g. all of 2024) are by construction not a field event; regional season
  outlook is out of scope for the per-field warning.
- Peer medians use only same-date observations, so no future information enters a label or feature.
- The validation gate passes for 7 and 14 days on Soest; the test-season result is reported once,
  in [baselines.md](../baselines.md).
