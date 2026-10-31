# Week 30 — "Fields needing a look" overview strip (US-44)

- What: Live header strip counts monitored fields by worst light (red/amber/
  green) and a button opens the field that needs it most.
- Hidden until spring risk data exists; fields without a light aren't counted.
- Verify: `vitest run src/live.test.ts`; e2e + a11y suites pass.
