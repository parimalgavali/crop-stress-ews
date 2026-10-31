# ADR 0048: Basemap style toggle

Status: Accepted (US-51, Issue #109)

## Context
Aesthetic round: the plain OSM streets base is noisy at low zooms and a
minimal/dark base reads better next to the three-light fields.

## Decision
- Three bases: OSM streets (default), CARTO light, CARTO dark — all raster,
  all free under attribution (OSM ©, CARTO © added for the two CARTO styles).
- The swap replaces only the `osm` raster source; field layers are untouched.
- Choice persists in `localStorage` (`cropews-basemap`).
- No satellite base: Esri World Imagery's terms for a public project are
  murky, and a second imagery source isn't needed next to the field photo.

## Consequences
- `Basemap`/`BASEMAPS` exported from `MapView`; chips overlay the map corner.
