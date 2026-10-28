# 0022 — Alerts through public ntfy.sh topics per field

Status: accepted (US-21, Issue #40).

## Context
Farmers want a message when a field turns red without checking the website. E-mail or Telegram
would need us to store addresses or chat ids, plus a mail provider or bot token.

## Options
| Option | Personal data stored | Secret needed | Cost |
|---|---|---|---|
| E-mail (SMTP provider) | e-mail addresses | yes | free tier limits |
| Telegram bot | chat ids | bot token | free |
| **ntfy.sh topic per field** | **none** | **no** | free |

## Decision
- Each Live field has the topic `cropews-nrw-<field_id>`. The Live card links to
  `https://ntfy.sh/<topic>`, where anyone can subscribe in the browser or the ntfy app (opt-in).
- On scheduled Pages runs, `scripts/send_alerts.py` compares the new `latest.json` with the last
  deployed one and posts one message per field whose earliest red horizon is new.
- The message is in English and German and uses the same reason texts as the UI, plus a note
  that it is a satellite-based estimate.

## Consequences
- Topics are public: anyone who knows a field id can read its alerts. That's fine, because the
  risk is already public on the website.
- No delivery guarantee; ntfy.sh is a free community service. If it fails, the step is skipped
  and the website still deploys.
