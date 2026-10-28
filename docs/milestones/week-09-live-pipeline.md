# Week 9 — Live pipeline for the 2026/27 season (US-15)

- New: `cropews.data.lwk` loads the current LWK `TSCHLAG` declared parcels (dl-de/by-2-0).
  `cropews.live` summarises the latest S2, S1 and DWD observations per parcel, and
  `scripts/live_update.py` writes `web/public/live/latest.json`.
- The Pages workflow runs the update every 5 days and deploys it. A failure in the live step
  still deploys the replay demo.
- UI: a **Live / Aktuell** toggle shows the data date and plain-language conditions per parcel,
  read aloud. No risk scores in winter (ADR 0015).
- Next: US-16 winter checks, US-17 check my field, and US-18 in-season winter-wheat mapping before 5 April 2027.
