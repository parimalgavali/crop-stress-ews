# 0016 — Winter checks: emergence vs peers and radar waterlogging

Status: Proposed (2026-10-28). Builds on [0010](0010-peer-reference-label.md). Results:
[winter_checks.md](../winter_checks.md).

## Context

The spring stress model (April–July) must not be applied in winter. Between sowing (October) and
spring restart (end of March) two problems matter in NRW: poor emergence and waterlogging after
heavy autumn rain (autumn 2023 before the wet 2024 harvest).

## Decision

- **Window:** 1 October of the year before harvest to 31 March (`WINTER_WINDOW`). Extractors take
  `--window winter`; output files carry a `_winter` suffix.
- **Emergence check** (`cropews.winter.emergence_scores`): clear Sentinel-2 dates from 1 November
  (October is skipped, sowing dates differ by weeks), NDVI departure from the same-date district
  median (ADR 0010), scaled per (district, 10-day bin) on training seasons only. A field is flagged
  "weak emergence" when the median winter z < −1.5 on at least 2 clear dates.
- **Waterlogging check** (`cropews.winter.wet_dates`): a radar date is "wet" when Sentinel-1 VV is
  ≥ 3 dB below the field's winter median for the same orbit direction and ≥ 20 mm of rain fell in
  the previous 7 days (DWD HYRAS). These thresholds are descriptive, not tuned.
- **Validation:** IACS has no emergence or flooding records, so both checks are related to the
  ADR 0010 spring stress label of the same field: event rate with vs without the flag and AUROC.
- **Live use** needs to know which current parcels are winter cereals; that comes with US-18.
  Until then the Live mode keeps descriptive observations only (ADR 0015).

## Consequences

- A flag is a "look at this field" hint, not a diagnosis; there is no ground truth for emergence
  or waterlogging in open data.
- Part of the emergence signal is a persistent field effect (weak fields stay weak), which is still
  useful because it is observed before 5 April.
