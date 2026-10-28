# Week 11 — In-season winter-wheat map (US-18)

- Extractors sample any arable crop (`--crops arable`) so training matches the Live population;
  72 district-season extractions (S1 + S2, winters 2019/20–2024/25, 60 parcels each).
- `cropews.cropmap`: monthly Oct–Mar features, one model per cutoff (1 Dec, 1 Feb, 1 Apr).
- Held-out 2024, 1 Apr: wheat AUROC 0.86 (recall 0.54 at p ≥ 0.5), any winter cereal 0.92.
  2025: 0.92 and 0.94. Per-district tables in [winter_wheat_map.md](../winter_wheat_map.md).
- Live: `--cropmap models` adds `wheat_p` and `spring_monitoring`; cards show
  "Probably (not) winter wheat (N% sure, satellite guess)" in EN/DE, read aloud.
- Model files published as release asset `cropmap-v1`, not committed.
