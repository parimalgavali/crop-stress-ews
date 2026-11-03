# ADR 0064: Deterministic weekly evidence digest

- Status: accepted, 2026-10-26
- Context: Dossier 6.2/P2 — a weekly report naming the fields to inspect, the dominant
  reason and data freshness, built from deterministic summaries of structured facts.
- Decision: `weeklyDigest(live, lang)` composes one plain sentence over the scouting
  queue: how many fields need a look, the most common first reason among queued fields
  (from each field's risk card at the queue's declared horizon) and the freshest clear
  satellite age from the evidence map. Shown under the overview counts; bilingual and
  part of the same lines family that feeds read-aloud. Observation recording stays in
  the per-field visit log (ADR 0060) — the queue buttons route to it. No LLM in the
  digest; a grounded summary model remains a separate evaluated experiment.
