# ADR 0055: Reproducible mini-run

- Status: accepted, 2026-10-26
- Context: Review finding 4.8 / spec 8.5 — the repo lacked a small offline run demonstrating the
  full causal chain for reviewers.
- Decision: `python -m cropews.demo_evaluation` builds a deterministic synthetic fixture (40
  fields, one district, Apr–Jun 2024, a quarter get two-step ndvi+ndmi dips) and runs peer
  scoring → event extraction → horizon labels → logistic baseline → AUROC per horizon →
  horizon-aware lead time, printing a run manifest (fields, events, AUROCs, warned events).
  No network, no licensed data; output is flagged `"synthetic": true`. Real data is never
  shipped; the manifest claims mechanics only, not model skill.
