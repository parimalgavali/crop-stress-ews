# 0018 — In-season winter-wheat map before crop declarations

Status: Proposed (2026-10-28). Builds on [0015](0015-live-season.md) and
[0016](0016-winter-checks.md). Issue #37. Results: [winter_wheat_map.md](../winter_wheat_map.md).

## Context

Crop declarations for harvest 2027 are published around May 2027, but spring forecasts start on
5 April 2027 and the winter checks (ADR 0016) only make sense among winter cereals. The Live
sample (ADR 0015) is a random sample of arable LWK parcels, so most of it is not winter wheat.

## Decision

- **Population:** past Europe-LAND parcels whose NRW crop code belongs to the LWK arable groups
  (`ARABLE_CROP_CODES`, derived from `lwk.ARABLE_USES`), so training matches the Live population.
  Extractors take `--crops arable`; files carry an `_arable` suffix and a `crops_*.parquet`
  sidecar with the declared crop code. 60 parcels per district and season, 6 core districts.
- **Window:** 1 October – 31 March before harvest (the US-16 winter window).
- **Features:** monthly medians (Oct–Mar) of Sentinel-1 VV, VH, VH/VV and of clear Sentinel-2
  NDVI, NDMI, plus the late-minus-early winter rise. Months without data stay missing.
- **Targets:** `y_wheat` (code 115) is used for spring monitoring; `y_cereal` (wheat, barley,
  rye, triticale) is reported because the winter checks apply to all winter cereals.
- **Split:** train 2020, 2021, 2023; model choice on 2022 only; held-out test 2024; extra
  check 2025. Logistic regression vs LightGBM, chosen by validation AUROC.
- **Cutoffs:** one model per cutoff (1 Dec, 1 Feb, 1 Apr), each trained only on the months
  observed by then. A single full-winter model scored almost all parcels below 0.5 before April.
  Before 1 December no guess is shown.
- **Reporting:** AUROC per split; precision, recall and F1 at p ≥ 0.5 per district.
- **Live use:** `live_update.py --cropmap` extracts images from 1 October and adds `wheat_p` to
  each parcel. Cards say "Probably (not) winter wheat (N% sure, satellite guess)" in EN/DE and
  read it aloud. `spring_monitoring` lists parcels with p ≥ 0.5; from 5 April that is the spring
  forecast set.
- **Model artefact:** the fitted bundle is not committed (`/models/` stays ignored); it is
  published as release asset `cropmap-v1` (`cropmap_y_wheat_<cutoff>.joblib`), which the Pages workflow downloads. Without it, Live
  runs as before.

## Consequences

- Early cutoffs are less accurate (wheat AUROC on 2024: 0.75 on 1 Dec, 0.83 on 1 Feb, 0.86 on
  1 Apr).
- Wheat vs barley/triticale is the hard part. In 2024 (late sowing after the wet autumn 2023)
  wheat recall at p ≥ 0.5 was 0.54; in 2025 it was 0.91. Any-winter-cereal reached AUROC 0.92.
- Parcels declared as wheat but sown late or failed may be missed; this is reported, not hidden.
