# ADR 0044: Printable one-page field report

Status: Accepted (US-47, Issue #101)

## Context
Farmonaut ships auto-generated farmer reports; interviewers and neighbours
expect something they can hold. A "Print this card" button plus a print
stylesheet gives that for free — no PDF service needed.

## Decision
- `window.print()` from a card button; `@media print` hides map, header,
  buttons, selects and hints, and lays the card out full-width.
- Print-only block adds provenance: site name, district, field id, the data
  date, and the field's deep link as text — the link has to be readable on
  paper, so no QR code (a QR would also need either a new dependency or an
  external service).
- The report is whatever the card shows — lines, weather strip, season chart,
  photo if loaded, the farmer's own "checked it" note.

## Consequences
- No new dependencies; the card stays the single source of truth.
