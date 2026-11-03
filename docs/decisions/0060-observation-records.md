# ADR 0060: Structured visit observation records

- Status: accepted, 2026-10-26
- Context: Dossier spec 8.3 — "what did someone actually find after the warning?" needs a
  structured visit record, not an automatic conversion of thumbs-up/down into ground truth.
- Decision: `observations.ts` stores device-local Observation records under
  `cropews.observations.v1` (same privacy model as field checks, ADR 0032): observed_at (the
  visit time, user-supplied — not the save time), observer_type, symptom, severity rubric
  (mild/moderate/severe, nullable — unknown is allowed), suspected_cause (free categories incl.
  "unknown" and "not_stress"), optional note/photo_ref, review_status starting "unreviewed".
  Export is a versioned JSON envelope (`schema_version`, exported_at, records) downloaded from
  the card's "Field visit record" section. Unknown/uncertain values are first-class; central
  sync is deferred to a real partner (bias and consent requirements in spec 8.3 remain open —
  sampling of non-alerted fields and adjudication are process, not code).
