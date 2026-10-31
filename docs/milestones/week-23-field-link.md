# Week 23 — A link per field (US-37)

- What: `?field=<id>` opens the app on that Live field; a copy-link button on each card.
- Why: the app should be shareable — for the demo video and for sending a field to someone.
- Verify: `cd web && npx playwright test e2e/app.spec.ts -g "shared"`.
- Out of scope: links into the 2024/2025 replay; a short-URL service.
