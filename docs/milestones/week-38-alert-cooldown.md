# Week 38: alert episode cooldown (US-63)

ntfy alerts now dedup by episode: alert_state rides on latest.json; re-alerts only after a
10-day cooldown once the field has gone non-red again.
