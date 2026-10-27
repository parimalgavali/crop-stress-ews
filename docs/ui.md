# Web UI (US-11)

Design: [ADR 0013](decisions/0013-one-screen-ui.md). Code: `web/`.

```bash
docker compose up -d --build && docker compose exec api python scripts/load_db.py   # API on :8000
cd web && npm install && npm run dev        # http://localhost:5173, proxies /api -> :8000

Static mode (GitHub Pages, [ADR 0014](decisions/0014-static-pages-demo.md)): build with `VITE_STATIC_DEMO=1` and the UI reads
`web/public/demo/<year>.json` (written by `scripts/export_static.py`) instead of calling the API.
npm test && npx playwright test             # unit + E2E (API mocked)
```

Flow: pick a field on the map or in the list → three traffic lights (7/14/21 days) with reasons →
"Listen" reads it aloud → "Play season" or the slider steps through the season. EN/DE toggle.
