# 0024 — Installable web app that works offline

Status: Accepted (2026-10-29). Story: US-24 (#55).

## Context
People check fields outdoors, often with poor mobile coverage. The site is static (ADR 0014), so it
can be made installable and usable offline without a server.

## Decision
- A web app manifest (`web/public/manifest.webmanifest`, relative `start_url`/`scope` so it works
  under `/crop-stress-ews/`) with plain traffic-light icons, so the site can be added to the
  home screen.
- A hand-written service worker (`web/public/sw.js`, ~50 lines, no new dependency), registered only
  in production builds:
  - pages: network first, cached page as fallback;
  - hashed `/assets/`: cache first;
  - other same-origin files (`live/latest.json`, `live/scoreboard.json`, `demo/*.json`, icons):
    network first, last copy as fallback.
  - Cross-origin requests (OpenStreetMap tiles, Planetary Computer, ntfy) are not touched. Bulk tile
    caching breaks the OSM tile policy, so offline the fields show on a blank map.
- Offline, the app shows "No internet. Showing the last saved data…" (EN/DE, symbol + words). This
  line is read aloud with the Live card. The existing "Data as of" date and the stale notice
  (ADR 0023) show how old the data is.

## Consequences
- Only data opened online at least once is available offline (e.g. a replay year never opened is not).
- Bump `CACHE` in `sw.js` to drop old caches if the caching rules change. Hashed assets need no bump.
- Playwright blocks service workers by default (they would bypass `page.route` mocks); the offline test
  allows them.
