# Week 8: Publish (US-13, part 1)

## What was done
- Rewrote the README for recruiters: problem statement, results table on the held-out 2024
  season, early-warning lead time, design rationale, a Mermaid architecture diagram, a UI
  screenshot, how to run the demo, and the full data pipeline.

## Why
A reviewer should understand the project and its honest limits in under a minute.

## How to verify
Read the README on GitHub; the Mermaid diagram renders natively.

## Part 2: live demo on GitHub Pages
- Hosting decision A (ADR 0014): static build that reads `web/public/demo/<year>.json`, deployed by
  `.github/workflows/pages.yml` on push to `main`. Chosen over Render/Fly.io (account, token,
  sleeping free tier).
- `scripts/export_static.py` + `cropews.static_demo` write the JSON from the served predictions;
  `web/src/api.ts` switches to it when built with `VITE_STATIC_DEMO=1`.
- Verify: `pytest tests/test_static_demo.py`, `npx vitest run`, then
  `VITE_STATIC_DEMO=1 npm run build && npx vite preview` and pick a field.

## Out of scope / next
- Demo goes live once the stacked PRs are merged to `main`.
- Regenerate the demo JSON after the six-district rerun.
- 2-minute video.
- Refresh the results table after the six-district rerun.
