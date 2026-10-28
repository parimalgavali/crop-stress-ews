# ADR 0032: "I checked it" button, saved only on the phone

Status: Accepted (US-35, Issue #77)

## Context
The forecast check (ADR 0020) only scores forecasts against satellite labels. A farmer who
walks a field knows something the satellite doesn't. Collecting these reports centrally would
need a server, accounts or device IDs, GDPR consent and moderation. This project has none of
those, and doesn't want to collect personal data (ADR 0022).

## Decision
- Each Live card has two big buttons: 👍 "Looks fine" and 👎 "Problem seen" (DE: "Sieht gut
  aus" / "Problem gesehen").
  - A check saves the date, the answer and the worst traffic light shown at that moment (or
    `null` before 5 April). It is stored under `localStorage["cropews.checks.v1"][field_id]`.
  - The card then shows "You checked it on 4 May: problem seen", with "Undo". The read-aloud
    includes that sentence.
- "Your checks agreed with the traffic light a of n times" counts only checks made while a
  light was shown. 👍 agrees with green, and 👎 agrees with amber or red.
- The card says "Saved only on this phone. Nothing is sent." No data leaves the browser.
  If storage is unavailable (private mode), the check is simply not kept.

## Consequences
- Each phone's checks stay on that phone. They are not added to the public forecast check,
  and clearing browser data deletes them.
- Central collection is left open. It would need a privacy design and a hosted backend first.
