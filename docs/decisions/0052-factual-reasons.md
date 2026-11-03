# ADR 0052: Reason text must not contradict observed data

- Status: accepted, 2026-10-26
- Context: Review finding 4.4 — reason strings are chosen from the *sign of a model
  contribution*, then phrased as physical facts; a rising ndvi_slope produced "Crop greenness is
  dropping". Missing-data claims fired without real missingness.
- Decision: `top_reasons` takes the raw feature rows; a group's physical text is emitted only when
  `kind:"fact"` validates against the raw values (ndvi_slope<0, any peer_anom<0, real missing
  indicator or days_since>15, water_balance_30d<0, hot_steps_30d>0). Otherwise a neutral
  attribution text ("X contributed to the estimate") is used and `kind:"attribution"`. Unverifiable
  groups (dry air, dry soil, canopy level, radar, stage) are always attribution.
- Notes: contributions remain base-model logits (pre-Platt); text stays factual EN/DE, no causal
  claims (drought/injury) are ever emitted.
