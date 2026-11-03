# ADR 0058: Budgeted scouting queue

- Status: accepted, 2026-10-26
- Context: Dossier spec 8.2 — "I can inspect a few fields today; which first?" Ranking must
  declare its horizon and budget, use a stable tie-breaker, keep unrankable fields visible,
  and be measurable on held seasons.
- Decision: `scouting.scout_queue` ranks scored fields by the declared 14-day risk
  (desc, field_id tie-break) up to budget 10. Fields with insufficient evidence or no 14-day
  forecast go to `unavailable` — shown, never treated as green. `payload.scouting` carries
  horizon, budget, queue and unavailable; the overview strip lists the queue with links.
  `queue_capture` + `scripts/scouting_eval.py` measure top-10 onset capture per date against
  persistence and random order on held seasons (proxy events — no claim about real stress).
- Result on the logged predictions: top-10 capture 11.8% (2024) / 32.1% (2025) vs 1.9%/1.0%
  persistence and 5.2%/5.6% random. The ranking carries signal beyond chance; absolute capture
  stays modest — reported as is.
