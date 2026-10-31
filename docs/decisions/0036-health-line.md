# ADR 0036: Show the data-health check on the Live site

Status: Accepted (US-39, Issue #85)

## Context
US-23 already writes a `health` block into `live/latest.json` (fields sampled, fields with
data, skipped Sentinel scenes, run time) and a CI job opens an issue on unhealthy runs.
The site itself never showed it, so users could not judge completeness.

## Decision
- `healthLine()` in `web/src/live.ts` renders "Data check: W of N watched fields have
  data" in the Live footer, plus the count of skipped satellite scenes.
- It warns (⚠ instead of ✓) under the same rule the pipeline uses: fewer than 50 % of
  fields with data, or any skipped scene (ADR 0023).
- Run time is deliberately not shown: it matters to the pipeline, not to the reader.

## Consequences
- The health block is now the single source of truth for both the CI issue and the site.
