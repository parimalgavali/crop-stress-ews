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
| [0016](0016-winter-checks.md) | Winter checks: emergence vs same-date peers, radar waterlogging after rain | Proposed |

Add a new numbered record for each decision that changes scope, data, labels, modeling or
evaluation. Amend the status of superseded records instead of deleting them.
| [0015](0015-live-season.md) | Live season 2026/27: current conditions for monitored LWK parcels, no winter model scores | Accepted |
| [0017](0017-check-my-field.md) | Check my field: Sentinel COG reads in the browser, weather from nearest monitored field | Accepted |
| [0018](0018-winter-wheat-map.md) | In-season winter-wheat map from Oct–Mar Sentinel-1/2, held-out 2024 | Proposed |
| [0019](0019-weather-forecast.md) | 5-day DWD ICON forecast shown on Live cards, evaluated but not a model input | Accepted |
| [0020](0020-forecast-log.md) | Prospective forecast log on the forecast-log branch, scored after the window | Accepted |
| [0021](0021-live-spring-risk.md) | Live spring risk from 5 April, model without AMBAV features | Accepted |
