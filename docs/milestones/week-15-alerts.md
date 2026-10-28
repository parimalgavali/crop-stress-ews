# Week 15 — Alerts (US-21)

- `cropews.alerts`: `new_red` (newly red fields only), bilingual `message` with UI reasons, `send` to ntfy.sh.
- `scripts/send_alerts.py` runs on scheduled Pages runs against the last deployed `latest.json`.
- Live card: "Get a message when this field turns red" link to the field's ntfy topic (ADR 0022).
