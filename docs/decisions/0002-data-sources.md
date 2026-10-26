# 0002 — Data sources, access and licences

Status: Accepted (2026-10-26)

| Source | Use | Access | Licence |
|---|---|---|---|
| Europe-LAND Harmonized IACS v1.3 (Zenodo 18670815), `DE_NRW` 2019–2025 | Field polygons + crop per year | Per-year geoparquet extracted from the zip with HTTP range requests (`scripts/download_nrw_fields.py`); full download is slow (~600 KB/s) | CC BY 4.0; cite original sources |
| Sentinel-2 L2A | Optical indices | Microsoft Planetary Computer STAC (no account) | Copernicus free and open |
| Sentinel-1 GRD/RTC | Cloud-independent signal | Planetary Computer | Copernicus free and open |
| DWD Climate Data Center | Weather, phenology | opendata.dwd.de | CC BY 4.0 |
| BKG VG2500/VG250 | District boundaries | daten.gdz.bkg.bund.de | dl-de/by-2-0 |
| IT.NRW harvest reports | District/state yields for label sanity checks | Yearly PDF reports; Regionalstatistik API needs free registration (guest access ended 2025) | Open, cite source |
| YieldSAT | Field-level yield validation | Request via yieldsat.github.io | To confirm on download |
| UFZ Drought Monitor | Optional soil-moisture cross-check | ufz.de | Non-commercial only, no redistribution |

## Notes

- Sentinel-2 processing baseline ≥ 04.00 (from Jan 2022) adds a −1000 DN offset; handled in
  `cropews.data.sentinel2.reflectance`.
- Field statistics use a 10 m inward buffer and the SCL band (4 vegetation, 5 bare soil = clear).
