# ADR 0062: Versioned import/export contract + simulated adapter

- Status: accepted, 2026-10-26
- Context: Dossier 6.4/P2 — make project data portable through a documented
  GeoJSON/CSV contract with explicit CRS, units and model-version metadata; a
  labelled simulated adapter demonstrates the schema without a live partner.
- Decision: `cropews/interchange.py` defines cropews-fields v1 (GeoJSON,
  EPSG:4326 required, hectares), cropews-scores v1 (CSV with a contract directive
  line, risk 0-1, issued_at/feature_cutoff mandatory) and cropews-observations v1
  (mirrors web `cropews.observations.v1`). Violations raise ContractError.
  `fixtures/adapter_demo/` holds a labelled simulated partner export mapped by
  `adapt_simulated_export` (schema mapping only, no reprojection). Observations
  import as evidence, never as ground truth (ADR 0060).
