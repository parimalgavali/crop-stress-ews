# Week 10 — Winter checks (US-16)

- Sentinel-1/2 extractors gained `--window winter` (1 October before harvest to 31 March).
- Extracted winter Sentinel-2 for 6 districts × 7 seasons (40 fields each) and winter Sentinel-1
  for 2024 (wet autumn 2023) and 2022 (comparison).
- `cropews.winter`: emergence check against same-date district peers (ADR 0010 residual) and a
  radar waterlogging check (VV drop after heavy rain).
- Results and limits in [winter_checks.md](../winter_checks.md); decision in
  [ADR 0016](../decisions/0016-winter-checks.md).
- Main finding: weak winter emergence is a useful early hint in most seasons (AUROC ~0.70 for a spring
  stress event) but not in the wet test season 2024.
- Next: US-17 check my field, US-18 in-season winter-cereal mapping (needed before the winter
  checks can run in Live mode).
