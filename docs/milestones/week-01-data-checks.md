# Week 1 — data checks and scaffold

## What was done

- Confirmed region (NRW), crop (winter wheat) and seasons (2019–2025); see decision 0001.
- Counted winter-wheat parcels per season and district from Europe-LAND `DE_NRW`.
- Measured Sentinel-2 clear observations for 60 Soest wheat fields in 2022 and 2024.
- Found that 2022 was a good wheat year in NRW, so the test season moved to 2024.
- Scaffolded the package, data contract, loaders, Sentinel-2 extractor, scripts, tests and CI.

## How to verify

`pytest -q` runs offline. The README quick start reproduces the field audit and a Sentinel-2
extraction (needs network).

## Out of scope for this milestone

Sentinel-1 and weather extraction, labels, models, API and UI.
