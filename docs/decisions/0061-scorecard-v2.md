# ADR 0061: Prospective scorecard v2

- Status: accepted, 2026-10-26
- Context: Dossier spec 8.4 — denominators must be explicit and a missing outcome needs a
  reason: still pending vs permanently unobservable (the label needs two clear dates, so a due
  horizon is not necessarily confirmable today).
- Decision: scoreboard emits `schema_version: 2` and per horizon: issued, eligible,
  withheld (stale-origin), pending (window not closed), evaluated, pending_outcome (due, no
  outcome row yet), unobservable (outcome row exists with NaN label), plus the existing scored
  metrics and a persistence-baseline AUROC (each scored forecast vs the same field's previous
  logged risk at that horizon). `no_outcome` is kept as pending_outcome + unobservable for old
  readers.
  `outcomes_long(keep_nan=True)` preserves NaN label rows; the offline outcomes.parquet on the
  forecast-log branch should be rebuilt with keep_nan=True for the split to appear on the live
  scoreboard (before that, unobservable reads 0 and pending_outcome absorbs both).
