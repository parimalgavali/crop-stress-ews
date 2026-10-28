# Week 22 — Accessibility checks in CI (US-36)

- What: every PR now runs axe (WCAG 2.1 A/AA) on the replay and Live cards, in English and
  German. Two problems it found were fixed (ADR 0033).
- Why: so the "simple for anyone" claim is tested on every change.
- Verify: in `web/`, `npm run build && npx playwright test e2e/a11y.spec.ts`. Set
  `AXE_DEBUG=1` to print the violations.
- Out of scope: Lighthouse, screen-reader and plain-language testing with real users.
