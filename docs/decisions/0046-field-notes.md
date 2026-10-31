# ADR 0046: Free-text field notes, device-local

Status: Accepted (US-49, Issue #105)

## Context
"I checked it" (ADR 0032) captures a 👍/👎, but a scout's real finding is
words: "wet at the lower end". OneSoil scouting attaches notes to fields.

## Decision
- `FieldCheck` gains an optional `note` (≤ 280 chars); an editable textarea on
  the card saves onto the latest check via `setNote`. Empty clears it.
- Same storage and privacy story as checks: `localStorage` only, the existing
  "Nothing is sent" line still applies. No sync — that would need a backend
  and a privacy design (ADR 0032).
- The note is read aloud with the check status.

## Consequences
- `cropews.checks.v1` schema gains an optional key — old entries load fine.
