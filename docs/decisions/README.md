# Decision records

| # | Decision | Status |
|---|---|---|
| [0001](0001-region-crop-seasons.md) | NRW winter wheat, seasons 2019–2025, test 2024 | Accepted |
| [0002](0002-data-sources.md) | Data sources, access routes and licences | Accepted |
| [0003](0003-code-licence.md) | Code licensed under MIT; datasets keep their own licences | Accepted |
| [0004](0004-sentinel1-rtc.md) | Sentinel-1 RTC backscatter per field (VV, VH, VH/VV in dB) | Accepted |
| [0005](0005-dwd-weather-grids.md) | Daily weather from DWD HYRAS + AMBAV 1 km grids per field | Accepted |
| [0006](0006-five-day-grid.md) | Regular 5-day grid with explicit observed masks, no forward-fill | Accepted |
| [0007](0007-stress-label.md) | Stress-onset label: Sentinel-2 anomaly vs training-only baseline | Accepted |
| [0008](0008-evaluation-protocol.md) | Evaluation protocol: season splits, validation-frozen thresholds, baselines | Accepted |
| [0009](0009-label-sanity-outcome.md) | Label tracks yield loss spatially, not across seasons; revise before US-09 | Accepted |
| [0010](0010-peer-reference-label.md) | Stress label against same-date district peers (replaces climatology reference) | Accepted |
| [0011](0011-sequence-models.md) | Sequence models: GRU-D and LSTM on causal windows, validation-only selection | Accepted |
| [0012](0012-api-and-demo-model.md) | API over precomputed predictions; demo uses calibrated logistic model with contribution-based reasons | Accepted |
| [0013](0013-one-screen-ui.md) | One-screen accessible UI: React/Vite/MapLibre, symbol+word lights, Web Speech read-aloud | Accepted |
| [0014](0014-static-pages-demo.md) | Live demo on GitHub Pages from a small precomputed JSON file (exception to the derived-data rule) | Accepted |
| [0016](0016-winter-checks.md) | Winter checks: emergence vs same-date peers, radar waterlogging after rain | Accepted |

Add a new numbered record for each decision that changes scope, data, labels, modeling or
evaluation. Amend the status of superseded records instead of deleting them.
| [0015](0015-live-season.md) | Live season 2026/27: current conditions for monitored LWK parcels, no winter model scores | Accepted |
| [0017](0017-check-my-field.md) | Check my field: Sentinel COG reads in the browser, weather from nearest monitored field | Accepted |
| [0018](0018-winter-wheat-map.md) | In-season winter-wheat map from Oct–Mar Sentinel-1/2, held-out 2024 | Proposed |
| [0019](0019-weather-forecast.md) | 5-day DWD ICON forecast shown on Live cards, evaluated but not a model input | Accepted |
| [0020](0020-forecast-log.md) | Prospective forecast log on the forecast-log branch, scored after the window | Accepted |
| [0021](0021-live-spring-risk.md) | Live spring risk from 5 April, model without AMBAV features | Accepted |
| [0022](0022-alerts-ntfy.md) | Alerts through public ntfy.sh topics per field | Accepted |
| [0023](0023-pipeline-health.md) | Live pipeline health: health block, pipeline-health issue, stale-data notice | Accepted |
| [0024](0024-installable-offline.md) | Installable web app: manifest and service worker with last-data fallback | Accepted |
| [0025](0025-incremental-live.md) | Incremental live extraction (observation cache) and 60 fields per district | Accepted |
| [0026](0026-yearly-retraining.md) | Yearly champion/challenger retraining of the Live risk model | Accepted |
| [0027](0027-season-chart.md) | Season greenness chart on Live cards: field vs district peer median since 1 October | Accepted |
| [0028](0028-field-photo.md) | Satellite photo of the selected Live field, read in the browser on request | Accepted |
| [0029](0029-dwd-phenology.md) | Nearby winter-wheat growth stage from DWD phenology observers on Live cards | Accepted |
| [0030](0030-bk50-soil.md) | BK50 soil on Live cards; tested as model input, not adopted | Accepted |
| [0031](0031-soil-moisture-forecast.md) | Soil-moisture trend on the forecast line; tested as model input, not adopted | Accepted |
| [0032](0032-checked-it.md) | "I checked it" button, saved only on the phone | Accepted |
| [0033](0033-a11y-ci.md) | Automated accessibility checks (axe, WCAG 2.1 A/AA) in CI | Accepted |
| [0034](0034-field-link.md) | `?field=` link opens the app on a chosen field | Accepted |
| [0035](0035-frost-card.md) | Frost note distinguishes protective snow from bare-ground hard frost | Accepted |
| [0036](0036-health-line.md) | Live footer shows the data-health check | Accepted |
| [0037](0037-district-calibration.md) | Per-district calibration tested and rejected | Rejected |
| [0038](0038-kndvi-label.md) | kNDVI stress labels tested and rejected | Rejected |
| [0039](0039-yieldsat.md) | YieldSAT outcome check blocked on gated access | Blocked |
| [0040](0040-frost-map.md) | Frost low-spot map not validatable with open data | Blocked |
| [0041](0041-overview-strip.md) | Live overview strip counts fields by worst light | Accepted |
| [0042](0042-weather-strip.md) | Live cards show a 5-day weather strip from daily ICON forecast | Accepted |
| [0043](0043-field-navigation.md) | Prev/next buttons walk Live fields in list order | Accepted |
