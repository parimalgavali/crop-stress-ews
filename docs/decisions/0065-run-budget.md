# ADR 0065: Monitoring/performance budget in the run report

- Status: accepted, 2026-10-26
- Context: Dossier P2 — a data-freshness, extraction-duration and cost report for the
  live pipeline. The health block already carried minutes; extraction cost and
  freshness were invisible without opening logs.
- Decision: `run_health` gains extraction_minutes (satellite/weather stage only),
  scenes_s2/s1 (rows read this run), cache_hit and freshest_s2. The Live health line
  adds "update took X min" (EN/DE). No cost in euros — runs are on free CI minutes,
  so cost is tracked as runtime and scenes read, not money.
