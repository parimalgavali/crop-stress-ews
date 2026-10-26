# Project memory

## Purpose

Portfolio project for applied-AI / AgriTech roles in Germany (target employers include xarvio/BASF
Digital Farming, Bayer Crop Science, CLAAS and the Agrotech Valley cluster). Not a thesis and not
a production product for farmers.

## Current decisions

- Region NRW, crop winter wheat, seasons 2019–2025 — [0001](decisions/0001-region-crop-seasons.md)
- Data sources and access — [0002](decisions/0002-data-sources.md)
- Test season is 2024 (wet year), not 2022: in NRW, 2022 was a good wheat year.
- Sentinel-1 RTC backscatter per field, ascending/descending kept separate — [0004](decisions/0004-sentinel1-rtc.md)
- Weather from DWD HYRAS + AMBAV 1 km daily grids at field points — [0005](decisions/0005-dwd-weather-grids.md)
- Code is MIT-licensed; datasets are not redistributed and keep their own licences — [0003](decisions/0003-code-licence.md)

## Week-1 data inspection results (2026-10-26)

| Year | Winter-wheat fields | Area (ha) | NRW yield (t/ha) |
|---|---:|---:|---:|
| 2019 | 71,421 | 244,865 | — |
| 2020 | 65,152 | 223,959 | 8.66 |
| 2021 | 64,911 | 222,794 | 7.93 |
| 2022 | 67,438 | 231,667 | ~8.9 (preliminary) |
| 2023 | 69,286 | 235,247 | 8.22 |
| 2024 | 54,384 | 188,218 | 7.02 |
| 2025 | 69,546 | 238,629 | ~9.0 (preliminary) |

- Median field size 2.4 ha; 59% of fields ≥ 2 ha.
- Largest wheat districts (mean ha): Soest 18.9k, Warendorf 16.2k, Höxter 16.1k, Coesfeld 15.5k,
  Düren 13.7k, Lippe 12.3k, Rhein-Erft 10.9k.
- Sentinel-2 cloud check (60 fields ≥ 2 ha near Soest, April–July, field clear if ≥ 80% of
  pixels are SCL 4/5): median 15 clear dates per field in 2022, 12 in 2024; median longest gap
  ~25 days. Sentinel-1 is needed for the 14/21-day horizons.

## Open questions / next steps

- Stress-label definition and its sanity check against district yields (week 2).
- Sentinel-1 (`scripts/extract_s1.py`) and DWD weather (`scripts/extract_weather.py`) extractors done.
- User stories are GitHub Issues (label `user-story`, milestones W1–W8), each linked to its branch and PR.
- Free Regionalstatistik account for automated district yields; until then use IT.NRW PDFs.
- YieldSAT access, licence and whether its German wheat fields are in NRW.
