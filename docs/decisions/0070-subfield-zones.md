# ADR 0070: Subfield anomaly view (spec 8.6)

- Status: accepted, 2026-10-26
- Context: spec 8.6 — retain clear-pixel index maps, form contiguous candidate zones,
  report unstable masks, cloud/shadow artefacts and pixels outside the usable field
  interior.
- Decision: for each Live field's freshest clear scene a 20 m NDVI cutout is kept.
  Pixels below (field clear-interior median − 0.15) are grouped into 4-connected
  zones ≥ 4 px and reported with area (ha) and mean delta. `mask_quality` reports
  clear vs cloud/shadow shares inside the buffered field interior and flags views
  under 50 % clear as unstable — shown as "the view is patchy" on the card.
  The map is downsampled to ≤ 28 cells/side for the payload; the card renders cells
  with weak patches in the warn colour plus a bilingual, read-aloud summary line.
