# 0017 — Check my field: Sentinel reads in the browser, weather from the nearest monitored field

Status: Accepted (2026-10-28). Builds on [0014](0014-static-pages-demo.md) and
[0015](0015-live-season.md).

## Context

US-17: a user draws a field in Live mode and gets the same current conditions as the 180 monitored
parcels. The demo is a static GitHub Pages site (ADR 0014), so there is no server to run the
Python extractors on demand.

Checked on 2026-10-28 with an `Origin: https://parimalgavali.github.io` header:

| Endpoint | CORS |
|---|---|
| Planetary Computer STAC search (POST) | `Access-Control-Allow-Origin: *` |
| Planetary Computer SAS token API | `*` |
| Sentinel-2 L2A and Sentinel-1 RTC COG blobs (range GET) | `*` |
| DWD opendata (HYRAS NetCDF) | none |

## Decision

- **In the browser, no backend:** STAC search for the last 60 days over the drawn polygon,
  anonymous SAS token, then range reads of the COGs with `geotiff` (MIT, 2.1.x).
  - Sentinel-2: SCL, B04 and B08 on a 20 m grid; clear = SCL 4/5 ≥ 0.8; NDVI median and the change
    against a clear view ≥ 20 days earlier, as in `cropews.live`.
  - Sentinel-1: VV median in dB, and the change against earlier views in the same orbit direction.
  - At most 12 Sentinel-2 and 8 Sentinel-1 scenes per check.
- **Weather:** DWD has no CORS, so rain and temperature come from the nearest monitored field in
  `live/latest.json` if it is within 15 km; otherwise the card says so.
- **Limits:** the polygon must lie inside the NRW extent of the LWK parcels and cover 0.5–500 ha.
  Problems (outside NRW, size, no data or clouds, network error) are shown in plain words.
- No winter checks or risk scores for drawn fields (ADR 0015, ADR 0016).

## Consequences

- No server cost, and it works on Pages. A check takes several seconds and depends on Planetary
  Computer's availability and its anonymous rate limits.
- The browser and Python code compute the same quantities twice. Unit tests pin the projection,
  the polygon mask and the NDVI offset handling.
