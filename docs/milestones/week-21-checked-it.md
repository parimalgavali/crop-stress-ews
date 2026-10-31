# Week 21 — "I checked it" button (US-35)

- What: after visiting a field, a farmer taps 👍 or 👎 on its Live card. The check is saved on the
  phone with the traffic light shown at the time, and can be undone. The card then says how
  often their checks agreed with the light (ADR 0032).
- Why: it adds what people actually saw to the satellite-only forecast check, without
  collecting personal data.
- Verify: in `web/`, `npm test` (fieldChecks, CheckedIt) and `npm run e2e`. The live test taps
  "Looks fine", reloads the page and checks that the note is still there.
- Out of scope: sending checks to a server, and adding them to the public scoreboard.
