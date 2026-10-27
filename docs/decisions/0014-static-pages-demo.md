# 0014 — Live demo on GitHub Pages from a small precomputed JSON file

Status: Accepted (2026-10-27). Builds on [0012](0012-api-and-demo-model.md) and [0013](0013-one-screen-ui.md).

## Context

US-13 needs a public demo link that a recruiter can open without setup. Two options were weighed:

| | A) GitHub Pages, static JSON | B) Render / Fly.io, full API + PostGIS |
|---|---|---|
| Cost / accounts | Free, no extra account | Free tier, needs the owner's account and an API token |
| Availability | Always on, CDN | Free tiers sleep; first load can take ~30–60 s |
| What runs | The same React UI, data read from `demo/<year>.json` | The real FastAPI + PostGIS stack |
| Maintenance | Rebuilt by a workflow on every push to `main` | Database must be reloaded and kept alive |
| Data in repo | One derived file per demo season (~0.1–1 MB) | None |

The project owner chose **A** (recommendation) on 2026-10-27.

## Decision

- `scripts/export_static.py` (logic in `cropews.static_demo`) turns the output of
  `scripts/export_predictions.py` into `web/public/demo/2024.json` and `2025.json`: dates, field
  polygons (EPSG:4326, 5 decimals ≈ 1 m), per field/date one `[days, risk, level, [reason codes]]`
  entry per horizon, reason texts once (EN/DE), and the source attribution.
- The UI reads these files when built with `VITE_STATIC_DEMO=1`; otherwise it calls the API as
  before. Worst-level-per-field and reason expansion are done client-side
  (`staticFields`, `staticRisk` in `web/src/api.ts`), mirroring the API.
- `.github/workflows/pages.yml` builds with `VITE_STATIC_DEMO=1` and
  `VITE_BASE=/crop-stress-ews/` and deploys to GitHub Pages on every push to `main`.
  URL: <https://parimalgavali.github.io/crop-stress-ews/>.
- **Exception to the "no derived data in git" rule, for these demo files only.** They contain only
  the demo-season predictions and the demo fields' polygons. All sources allow redistribution with
  attribution (Europe-LAND IACS CC BY 4.0, Copernicus free and open, DWD CC BY 4.0). No UFZ data is
  included. Raw data, Parquet, models and other outputs stay ignored.
- The FastAPI + PostGIS stack (ADR 0012) remains the reference backend for local runs and CI.

## Consequences

- The demo never sleeps and costs nothing; anyone can verify it without credentials.
- The demo files must be regenerated and committed whenever the served predictions change
  (e.g. after the six-district rerun).
- A static demo cannot show live inference; neither can the API (ADR 0012), so nothing is lost.
