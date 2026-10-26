# crop-stress-ews

Crop-stress early-warning system for **winter wheat in North Rhine-Westphalia (NRW)**.
Given a field and a date, it will predict the risk of crop stress 7, 14 and 21 days ahead from
Sentinel-1/2 satellite data and DWD weather, explain why, and show it in a one-screen web app.

> Status: week 1 of 8 — data pipeline scaffold. See [`docs/project_memory.md`](docs/project_memory.md).

## Scope at a glance

| | |
|---|---|
| Region | NRW, core districts Soest, Warendorf, Höxter, Coesfeld, Düren, Rhein-Erft-Kreis |
| Crop | Winter wheat (`winter_common_soft_wheat`, NRW code 115) |
| Seasons | 2019–2025; prediction window 1 April – 31 July |
| Splits | train 2019–2021 + 2023, validate 2022, **test 2024 (wet year)**, extra check 2025 |
| Fields | ~54k–71k winter-wheat parcels per year (Europe-LAND IACS, CC BY 4.0) |

## Quick start

```bash
pip install -e ".[dev,extract]"
pre-commit install

# 1. Field parcels (≈350 MB per year, extracted from the Zenodo zip by range requests)
python scripts/download_nrw_fields.py --years 2022 2024

# 2. District boundaries: BKG VG2500 (dl-de/by-2-0)
curl -L -o data/raw/vg2500.zip https://daten.gdz.bkg.bund.de/produkte/vg/vg2500/aktuell/vg2500_12-31.utm32s.shape.zip
unzip data/raw/vg2500.zip -d data/raw/vg2500

# 3. Audit and a first Sentinel-2 extraction
python scripts/audit_fields.py --districts data/raw/vg2500/vg2500/VG2500_KRS.shp
python scripts/extract_s2.py --year 2024 --district Soest --n 60 \
    --districts data/raw/vg2500/vg2500/VG2500_KRS.shp
```

## Layout

```
src/cropews/        config, data loaders, data contract, Sentinel-2 extraction
scripts/            command-line entry points
tests/              offline unit tests (no network)
docs/               project memory, decisions, data contract, scope, milestones
```

## Data sources and licences

Europe-LAND Harmonized IACS inventory (CC BY 4.0, cite original sources), Copernicus Sentinel-2
via Microsoft Planetary Computer, BKG administrative boundaries (dl-de/by-2-0), DWD Climate Data
Center (CC BY 4.0), IT.NRW harvest statistics. Details: `docs/decisions/0002-data-sources.md`.
