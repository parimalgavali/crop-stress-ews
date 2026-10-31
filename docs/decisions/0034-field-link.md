# ADR 0034: A link that opens the app on a chosen field

Status: Accepted (US-37, Issue #81)

## Context
The app is meant to be shown and shared. Until now there was no way to point someone at a
specific field: the URL was always the same.

## Decision
- `?field=<field_id>` in the URL opens the app in Live mode with that field selected
  (`web/src/fieldLink.ts`). Selecting a field updates the address bar with
  `history.replaceState`, so copying the address always gives a link to what is on screen.
- Each Live card has a "🔗 Link to this field" button (`navigator.clipboard`, with a
  `window.prompt` fallback where the clipboard is unavailable, e.g. non-HTTPS).
- An id that is not in the current Live sample shows "This field is not monitored. Please
  pick one from the list." instead of a broken card.
- Only Live fields are linkable; the replay is a fixed demonstration and its ids are not
  stable across exports.

## Consequences
- Links keep working while a field stays in the seasonal sample (US-26 keeps it stable).
  A link to a removed field degrades to the hint above, not to an error.
- Works on the static Pages site and in the installed PWA: the service worker serves the
  app shell for any path, and the parameter is read client-side.
