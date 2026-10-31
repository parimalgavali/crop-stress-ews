# ADR 0043: Previous/next field buttons on the Live view

Status: Accepted (US-46, Issue #99)

## Context
OneSoil's mobile app walks fields sequentially; our users had to re-open the
field list or hunt on the map for every field.

## Decision
- ◀ / ▶ buttons under the field list step through `options` — the same order
  as the list itself (worst light first, then field id), so a reader starts
  where it matters.
- Live view only: replay already has its own date list workflow.
- With nothing selected, "Next" opens the first field (the worst one);
  buttons disable at the ends — no wrap-around, keeps position obvious.

## Consequences
- Deep link (?field=) and read-aloud keep working: it's only `setSelected`.
