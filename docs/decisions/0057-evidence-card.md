# ADR 0057: Evidence and data-quality card

- Status: accepted, 2026-10-26
- Context: Dossier spec 8.1 — a warning must show how old and how thin its evidence is. Model
  risk, data quality and crop eligibility stay separate; a high risk is not high confidence.
- Decision: `live.evidence(field_id)` emits a per-field record into `payload.evidence`:
  crop_status (wheat map), model_version, issued_at, feature_cutoff, last_clear_s2_at (+ age,
  clear fraction), last_s1_at, weather_available_through, usable_peer_count (same-district
  peers with a clear view ≤15 d), quality_status and quality_reasons. Null means unknown —
  never zero or healthy.
  Status rules: `insufficient` when no optical or no weather; `limited` for stale optical
  (>15 d), missing radar, weather ending >2 d before as_of, fewer than 5 usable peers, or an
  unconfirmed crop; else `ok`.
  The card shows the facts and status in an expandable "Evidence" section (EN/DE, factual
  wording, read aloud as one label); no second risk calculation in TypeScript.
