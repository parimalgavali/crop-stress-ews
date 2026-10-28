# Week 17 — Satellite photo of the field (US-31)

- What: "Show satellite photo" on each Live card loads the true-colour Sentinel-2 image of the
  card's last clear date, cut to the field border, with date, source and alt text (ADR 0028).
- Why: a farmer can see where in the field a weak patch is, instead of trusting a number.
- Verify: in `web/`, `npm test` (`fieldPhoto.test.ts`, `FieldPhoto.test.tsx`) and `npm run e2e`.
  For real data, run a local `scripts/live_update.py`, copy its JSON to `web/public/live/latest.json`,
  `npm run build && npx vite preview`, select a field and press the button.
- Out of scope: picking another date, false-colour views, offline caching of photos.
