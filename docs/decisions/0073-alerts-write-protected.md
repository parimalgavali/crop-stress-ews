# 0073 — Alerts only on write-protected ntfy topics

Status: accepted (Issue #165). Amends [0022](0022-alerts-ntfy.md).

## Context
Topics are `cropews-nrw-<field_id>` and field ids are public (`latest.json`, Live card). On an
open ntfy.sh topic anyone can post, so a stranger could send farmers a fake red alert or a fake
all-clear that looks like ours.

## Decision
- `send()` posts with `Authorization: Bearer $NTFY_TOKEN` to `$NTFY_URL` (default ntfy.sh).
  Without a token it sends nothing (fail closed); a non-https `NTFY_URL` is refused so the
  token never travels in plain text.
- The ntfy server must only let that token write `cropews-nrw-*`; everyone else read-only.
  Either reserve the topics on an ntfy.sh account, or self-host ntfy with
  `auth-default-access: deny-all`, a publisher user with write on `cropews-nrw-*` and
  `everyone` read on `cropews-nrw-*`.
- Pages workflow: secret `NTFY_TOKEN`, repository variable `NTFY_URL`. The web build gets
  `VITE_NTFY_URL` from the same variable; the Live card shows the subscribe link only when it
  is set.

## Consequences
- Alerts and the subscribe link are off until the owner sets up the protected server/topics.
- Old subscriptions to open ntfy.sh topics stay spoofable; they receive nothing from us.
