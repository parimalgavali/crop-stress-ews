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
- 5-day grid (t − 5 d, t], satellite values never forward-filled, `*_observed`/`*_days_since` masks — [0006](decisions/0006-five-day-grid.md)
- Stress label: NDVI/NDMI z < −1.5 vs training-only (district, 10-day bin) baseline, ≥ 2 clear dates, onset ≤ 30 June — [0007](decisions/0007-stress-label.md), [labels](labels.md)
- Label sanity outcome: tracks yield loss within seasons (ρ −0.46), not across seasons; revise before US-09 — [0009](decisions/0009-label-sanity-outcome.md), [results](label_sanity.md)
- Stress label reference: same-date district peers, not climatology (removes dry-spring season shifts) — [0010](decisions/0010-peer-reference-label.md)
- Sequence models: GRU-D + LSTM on causal windows, mask + time gaps, validation-only selection, Platt calibration; torch in optional `seq` extra — [0011](decisions/0011-sequence-models.md)
- API serves precomputed test/extra-season predictions from the validation-calibrated logistic model; reasons = summed logistic contributions; red/amber at 90%/75% validation specificity — [0012](decisions/0012-api-and-demo-model.md)
- UI: one screen (map + accessible field list + timeline), colour never alone (symbol + word), Web Speech read-aloud EN/DE, Playwright E2E with mocked API — [0013](decisions/0013-one-screen-ui.md)
- Live demo: GitHub Pages static build reading committed `web/public/demo/<year>.json` (only exception to the no-derived-data rule); FastAPI + PostGIS stays the local/CI backend — [0014](decisions/0014-static-pages-demo.md)
- Live season 2026/27: Pages job every 5 days writes `live/latest.json` (180 arable LWK parcels, observations only; forecasts from 5 April 2027) — [0015](decisions/0015-live-season.md)
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

## US-13 live demo hosting (decided 2026-10-27)

Options presented to the owner:

- **A) GitHub Pages + precomputed JSON (chosen, recommended).** Free, no accounts, never sleeps.
  The same React UI loads `demo/2024.json` / `demo/2025.json` (demo fields, dates, 7/14/21-day
  risk, level, reason codes, EN/DE texts, attribution). Needs one exception to the
  "no derived data in git" rule, for these files only; sources allow redistribution with credit.
- **B) Render / Fly.io with the full FastAPI + PostGIS stack (rejected).** Needs the owner's
  account and an API token; free tiers sleep, so the first load is slow; DB must be reloaded.

How it works:

- Generate: `python scripts/export_predictions.py && python scripts/export_static.py`
  (writes `web/public/demo/<year>.json`; commit them).
- Build: `VITE_STATIC_DEMO=1 VITE_BASE=/crop-stress-ews/ npm run build` in `web/`.
- Deploy: `.github/workflows/pages.yml` on every push to `main` (Pages source = GitHub Actions).
- URL: https://parimalgavali.github.io/crop-stress-ews/ (live once the stacked PRs reach `main`).
- Regenerate the JSON after any change to served predictions. Current JSON: six districts, 190 fields per season (~0.64 MB each).
- Details and trade-off table: [ADR 0014](decisions/0014-static-pages-demo.md).

## Open questions / next steps

- W9 live season (Issues #34–#40): US-15 live pipeline done (ADR 0015). Next: US-16 winter checks (emergence, waterlogging), US-17 check my field, US-18 in-season winter-wheat mapping (needed before 5 April 2027), US-19 forecast weather, US-20 prospective forecast log, US-21 alerts. LWK `TSCHLAG` = current declared parcels (dl-de/by-2-0); HYRAS current-year file is updated daily; AMBAV is monthly.
- US-16 winter checks (Issue #35, ADR 0016, [winter_checks.md](winter_checks.md)): extractors take `--window winter` (1 Oct – 31 Mar, `_winter` files in `data/interim/s2w`, `s1w`). Emergence peer-z flag: spring event rate 0.43–0.69 flagged vs 0.12–0.19 others, AUROC 0.69–0.75, but fails in test 2024 (0.56; cloudy winter, problems came in spring). Waterlogging = VV drop ≥ 3 dB after ≥ 20 mm/7 d rain; flags 124/240 fields in winter 2023/24 vs 28/240 in 2021/22, but does not predict which field gets a spring event. Live use waits on US-18 (which current parcels are winter cereals).
- US-18 winter-wheat map (Issue #37, ADR 0018, [winter_wheat_map.md](winter_wheat_map.md)): training population = arable Europe-LAND parcels (`ARABLE_CROP_CODES`, matches LWK `ARABLE_USES`), files in `data/interim/s1wa`, `s2wa` with `crops_*.parquet`. One model per cutoff (1 Dec/1 Feb/1 Apr) because a full-winter model collapses to p≈0 before April. Test 2024 at 1 Apr: wheat AUROC 0.86 but recall 0.54 (late sowing after wet autumn 2023), winter cereal AUROC 0.92; 2025: 0.92/0.94. Model bundles are joblib files in `/models/` (ignored), published as release asset `cropmap-v1`; Pages workflow downloads them and passes `--cropmap models`. No guess before 1 Dec. S1 winter extraction ≈1 h per district-season.
- US-19 weather forecast (Issue #38, ADR 0019, [weather_forecast.md](weather_forecast.md)): DWD ICON via Open-Meteo (CC BY 4.0, CORS, non-commercial free tier). Archived runs with lead time only from Feb 2024. Perfect-forecast features add nothing on 2022, so the risk model is unchanged; the forecast is display context only (`forecast[district]` in `latest.json`). Archive cached in `data/interim/forecast/icon_<district>_<year>.parquet`.
- US-20 forecast log (Issue #39, ADR 0020, [forecast_log.md](forecast_log.md)): append-only `forecasts.csv` on orphan branch `forecast-log` (never `main`), written by scheduled/manual Pages runs (`contents: write`). Scored only after `date + horizon` with outcomes from `outcomes.parquet` on the same branch. 2025 replay = offline AUROC exactly. Filling it needs live spring scoring, US-22 (Issue #46).
- US-14 six-district rerun (Issue #31; Sentinel-1 42/42 done): test 2024, 190 fields. Served logistic AUROC 0.74 / 0.80 / 0.77 (7/14/21 d) vs persistence 0.72 / 0.72 / 0.70; best research model GRU-D 30-day window 0.83 / 0.81 / 0.80. CIs still overlap persistence (ADR 0008 gate not met). Red alarms before 21/29 onsets, median 15 d. Sentinel-1 ablation no longer shows an effect on validation (test −0.03 only), so the earlier "Sentinel-1 matters most" Soest claim is withdrawn. Düren had no 2024 onsets; Coesfeld has many false alarms. Next: 2-minute video; per-district calibration is a candidate improvement (choose on validation).
- Label sanity check done (US-07, [week 3](milestones/week-03-label-sanity.md)); next: revised label ADR chosen on 2022, then US-09.
- US-13 README rewritten (results table, architecture diagram, UI screenshot `docs/img/ui.png`, full pipeline). Live demo decided and built (see below); 2-minute video still open.
- US-12 error analysis + model card ([error_analysis.md](error_analysis.md), [model_card.md](model_card.md)): Soest 2024 red alarms preceded 6/9 onsets (median 17.5 d); sensitivity drops with long S2 cloud gaps. Superseded by US-14 six-district numbers.
- US-11 UI done ([ui.md](ui.md)): `web/` React + Vite + MapLibre; CI job `web` runs tsc, eslint, vitest, Playwright. Node 20 via nvm locally.
- US-10 API done ([api.md](api.md)): FastAPI + PostGIS + Alembic, `docker compose up`; API tests run against a PostGIS service in CI. Next: US-11 UI.
- US-09 sequence models ([results](sequence_models.md)): on Soest on par with LightGBM (validation-selected LSTM, test 7 d AUROC 0.77; GRU-D 0.82), Sentinel-1 is the most useful input group; CIs overlap. Next: six-district rerun, then US-10.
- US-08b revised label (peer reference): Soest test 2024 LightGBM 0.80 vs persistence 0.66 AUROC at 7 d, logistic best at 14/21 d; CIs still overlap (40 test fields). Next: rerun on all six districts once Sentinel-1 is extracted, then US-09.
- US-08 baselines ([docs/baselines.md](baselines.md), ADR 0008): on Soest (40 fields/season) LightGBM does not beat persistence (test AUROC 0.71–0.76 vs 0.75–0.79, CIs overlap); the gate says revisit the label before US-09. Weather-only rule ≈ chance.
- Sentinel-1, DWD weather and 5-day grid done ([week 2](milestones/week-02-extractors-and-grid.md)); stress label implemented (US-06).
- User stories are GitHub Issues (label `user-story`, milestones W1–W8), each linked to its branch and PR.
- District yields: Landesdatenbank NRW table 41241-03i (open CSV, dl-de/by-2-0), no account needed.
- YieldSAT access, licence and whether its German wheat fields are in NRW.

## US-17 check my field (ADR 0017)

- Browser-only: Planetary Computer STAC search, SAS token and S2/S1 COG blobs allow CORS `*`
  (checked 2026-10-28); DWD opendata does not, so weather comes from the nearest monitored field
  within 15 km of `live/latest.json`.
- `web/src/checkField.ts` mirrors `cropews.live`: S2 SCL 4/5 ≥ 0.8 clear, NDVI on a 20 m grid with
  the baseline-04.00 offset, change against a clear view ≥ 20 days earlier; S1 VV dB change vs
  earlier same-orbit views. `geotiff` 2.1.3 (MIT) for range reads; own UTM projection tested
  against pyproj.
- Drawn fields: NRW extent of the LWK parcels, 0.5–500 ha; a real check took about 10 s.
