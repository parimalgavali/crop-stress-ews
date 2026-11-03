# Data import/export contract (dossier 6.4, P2)

Versioned interchange so field boundaries, risk scores and visit observations can
leave and enter the system with explicit coordinate reference system, units and
model-version metadata. Implemented in `src/cropews/interchange.py`
(`ContractError` on any violation) and `scripts/import_validate.py`.

## cropews-fields v1 — GeoJSON

- `contract`: `"cropews-fields"`, `contract_version`: `1`
- `crs`: name `urn:ogc:def:crs:EPSG:4326` — required; any other CRS is rejected
- `units.area_ha`: `hectare`
- Feature `properties`: `field_id` (required), `district`, `crop`, `area_ha`
- Geometry: `Polygon` or `MultiPolygon` only
- `produced_at`: ISO-8601 timestamp of the export

## cropews-scores v1 — CSV

- First line is the contract directive:
  `# contract=cropews-scores version=1 units=risk:0..1,horizon_days:days date:ISO-8601`
- Required columns: `field_id,date,horizon_days,risk,level,model_version,issued_at,feature_cutoff`
- `risk` is unitless, 0–1; `issued_at`/`feature_cutoff` required on every row so a
  score can never be read as known-before-issuance.

## cropews-observations v1 — JSON

- Mirrors the web app's `cropews.observations.v1` export envelope:
  `{schema_version: 1, exported_at, records: [...]}`, or a bare record list.
- Each record: `field_id`, `observed_at` (ISO-8601), `observer_type`, `symptom`,
  `severity` (nullable), `suspected_cause`, `review_status` — closed vocabularies,
  same values as `web/src/observations.ts`.
- Observations import as evidence records, never as ground truth (ADR 0060).

## Simulated adapter

`fixtures/adapter_demo/simulated_fields.json` is a clearly labelled **simulated**
partner export (`adapter: "agriconnect-simulated-v1"`, German property names, no
contract metadata). `adapt_simulated_export()` maps it into cropews-fields; the
result passes `import_fields_geojson`. A real adapter would also reproject
coordinates — this one demonstrates schema mapping and validation only.

    python scripts/import_validate.py fixtures/adapter_demo/simulated_fields.json --kind adapter
