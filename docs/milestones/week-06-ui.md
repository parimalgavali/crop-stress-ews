# Week 6 — One-screen UI (US-11)

## What was done

React/TypeScript/Vite app in `web/`: MapLibre map coloured by worst-horizon level, accessible field
list, 7/14/21-day traffic lights with symbols, words and reasons, EN/DE read-aloud, season replay
([ADR 0013](../decisions/0013-one-screen-ui.md), [ui.md](../ui.md)).

## Why

The project's differentiator is a warning that non-experts understand at a glance or by ear.

## How to verify

`cd web && npm ci && npx tsc -b && npx eslint . && npx vitest run && npx playwright test`
(CI job `web`). Manual run: see [ui.md](../ui.md).

## Out of scope / next

Six-district data once Sentinel-1 is complete; US-12 deployment and replay polish.
