# 0023 — Live pipeline health checks and stale-data notice

Status: accepted (US-23, Issue #52).

## Context
The first Pages run after the live-season merges deployed without Live data: one unreadable
Sentinel-1 tile ended the live step, and because that step is `continue-on-error`, the run
still showed green. Nobody was told, and the site kept no sign that its data was missing or old.

## Decision
- `live_update.py` adds a `health` block to `latest.json`: parcels sampled, parcels with data,
  Sentinel-1/2 scenes skipped after `READ_ATTEMPTS` failed reads, and run time in minutes.
- On scheduled and manual runs, `scripts/check_live_health.py` fails if `latest.json` is
  missing or fewer than half (`MIN_DATA_SHARE`) of the sampled parcels have data.
- If the live step failed or the check fails, the workflow opens a GitHub Issue labelled
  `pipeline-health`, or comments on the one already open. The next healthy run closes it.
  GitHub notifies the repository owner, so no extra alerting service or secret is needed.
- The Live screen shows a plain-words notice (English/German, also read aloud) when the data is
  more than 7 days old (`STALE_DAYS`); runs are every 5 days, so one missed run is tolerated.

## Consequences
- The workflow needs `issues: write`.
- Push deploys reuse the deployed data (ADR 0022 fix) and are not checked.
- An unhealthy run redeploys the previous `latest.json`, so the site keeps the last good data
  with the stale notice instead of going blank. It skips the forecast log and alerts, so old
  forecasts are not logged twice and no alert is sent from old data.
