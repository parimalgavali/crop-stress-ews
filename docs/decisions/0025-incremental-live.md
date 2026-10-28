# ADR 0025: Incremental live extraction and 60 fields per district

Status: Accepted (US-27, Issue #61)

## Context
Each live run re-read every Sentinel-1/2 scene since the window start (1 October once the wheat
map is active). At ~60 days a run takes ~25 min for 180 fields; at ~270 days (June) it would reach
the live step's 120-minute timeout. 30 parcels per district also leave few winter-cereal peers for
the winter cards (ADR 0016).

## Decision
- `scripts/live_update.py --cache DIR` keeps the selected S2/S1 observations (`s2.parquet`,
  `s1.parquet`) and `meta.json` (`start`, `through`, `fields`). The Pages workflow restores it with
  `actions/cache/restore` and saves it with `actions/cache/save`. It only does this on healthy
  scheduled/manual runs, so a broken run can't poison the cache.
- A district re-reads scenes only from `through − 10 days` if the cache covers all its fields, the
  window start, and a date not after `as_of` (`cache_since`). Otherwise it does a full read. The
  10-day overlap gives late or skipped scenes another chance. New rows replace cached rows with the
  same key (`merge_cached`).
- Weather (DWD grids) is still read in full; it is cheap.
- 60 parcels per district (`--n 60`). `stable_sample` (ADR 0015) orders parcels by hash, so the
  30 parcels already monitored stay in the 60.

## Consequences
- If the cache is missing (evicted after 7 days unused, a new key, an unreadable file), the run is
  full and slower, but still correct.
- The cached rows are the per-scene selections, so a code change to S1/S2 selection only applies to
  new rows. To force a full read, bump the cache key prefix in `pages.yml`.
