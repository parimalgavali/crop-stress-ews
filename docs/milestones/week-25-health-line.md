# Week 25 — Data-health line on the Live site (US-39)

- What: the Live footer shows "Data check: W of N watched fields have data" and flags
  skipped satellite scenes or an unhealthy run.
- Why: users should see the same completeness signal the pipeline monitors (ADR 0023).
- Verify: `vitest run src/live.test.ts`; footer test id `live-health`.
- Out of scope: run duration on the site; historical health trends.
