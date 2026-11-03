# ADR 0059: Alert episode cooldown

- Status: accepted, 2026-10-26
- Context: Dossier P1 — false-alert episode handling. `new_red` fired on every red transition,
  so a field flapping red -> green -> red across 5-day runs re-alerted subscribers each time.
- Decision: `alert_state` is persisted on the latest.json payload itself (the run already
  passes the previous latest.json to send_alerts, so it is the natural state channel).
  send_alerts stamps `{field_id: {last_alert_at: as_of}}` for each alerted field after every
  run — including dry runs, since the state reflects "would have alerted".
  A field alerts when it is red now, was not red in the previous run, AND its last alert is
  absent or >= COOLDOWN_DAYS (10) ago. A flap back to red inside the cooldown is the same
  episode and is suppressed; a fresh red after the cooldown is a new episode and alerts again.
