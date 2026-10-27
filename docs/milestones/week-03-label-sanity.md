# Week 3 — Label sanity check (US-07)

## What was done

| Story | PR | Output |
|---|---|---|
| US-07 Label sanity report | this PR | `scripts/download_yields.py`, `scripts/label_sanity.py`, [label_sanity.md](../label_sanity.md) |

Sentinel-2 was extracted for 30 wheat fields per district-season in the five other core districts
(Soest already had 40), labels built per district, and event shares compared with IT.NRW district
yields (open CSV, no account needed).

## Why

ADR 0007 made the label conditional on agreeing with an independent yield signal. Without that
check, any model metric would only measure how well we predict our own proxy.

## Result

Within a season, districts with more events lose more yield (ρ −0.46, p 0.003); across seasons
the label is driven by dry springs that do not cost yield. Decision: [ADR 0009](../decisions/0009-label-sanity-outcome.md).

## How to run

```bash
KRS=data/raw/vg2500/vg2500/VG2500_KRS.shp
python scripts/download_yields.py
for d in Soest Warendorf Höxter Coesfeld Düren Rhein-Erft-Kreis; do
  for y in 2019 2020 2021 2022 2023 2024 2025; do
    python scripts/extract_s2.py --year $y --district $d --n 30 --districts $KRS
  done
  python scripts/build_labels.py --district $d
done
python scripts/label_sanity.py
```

## Out of scope

Field-level yield validation (YieldSAT access pending), label revision (next ADR), Sentinel-1 for
the new districts (running, needed for the multi-district US-08 rerun).
