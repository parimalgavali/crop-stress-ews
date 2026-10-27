# 0013 — One-screen, low-literacy-friendly web UI

Status: Accepted (2026-10-27). Uses [0012](0012-api-and-demo-model.md).

## Context

US-11: a non-expert must understand a field's warning without reading charts.

## Decision

- **One screen, no navigation:** map + field panel + season timeline. React 18 + TypeScript + Vite
  in `web/`, MapLibre GL with OpenStreetMap raster tiles (attribution shown).
- **Never colour alone:** each horizon shows a coloured dot, a symbol (✓ / ! / ‼), a word
  ("Low risk / Watch / High risk") and, when not green, up to two reasons.
- **Read aloud:** browser Web Speech API (`de-DE` / `en-GB`, rate 0.9); one sentence per horizon,
  then the reasons for the worst horizon. No server-side TTS.
- **Accessible alternative to the map:** a native `<select>` listing fields worst-first, so the app
  works with keyboard and screen readers; ≥ 48 px targets, visible focus ring, `aria-live` card.
- **Replay:** play button and slider over the precomputed dates (2024 test, 2025 extra season).
- **Tests:** Vitest + Testing Library for components/speech text; Playwright E2E with the API
  mocked via `page.route` (no backend or tiles needed in CI).

## Consequences

- Speech quality depends on the voices installed in the user's browser/OS.
- The map is mouse/touch only; the list is the keyboard path.
