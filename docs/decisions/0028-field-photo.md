# ADR 0028: Satellite photo of the selected Live field

Status: Accepted (US-31, Issue #69)

## Context
Field-monitoring apps (OpenFarm, Epic Fields, OneSoil) show the field's latest clear true-colour
image. A farmer trusts a photo of their own field more than a number, and can see whether a weak
patch is a corner, a strip or the whole field. "Check my field" already reads Sentinel-2 COGs from
Planetary Computer in the browser (ADR 0017, CORS checked).

## Decision
- The Live card has a "Show satellite photo" button. Nothing is downloaded until it is pressed.
- `fieldPhoto(ring, date)` searches `sentinel-2-l2a` on the card's last clear date (`s2_date`). It
  then reads a window of the `visual` (TCI, 8-bit RGB, 10 m) asset with `geotiff` and makes pixels
  whose centre is outside the field border transparent (`maskRgb`). Fields wider than 160 pixels
  are read on a coarser grid.
- The ring is the exterior of the largest polygon of the field (`outerRing`); holes are ignored.
- The photo is drawn on a canvas with `role="img"` and an EN/DE alt text with its date. The caption
  names Copernicus Sentinel-2 and says how to read the colours. If there is no image or a network
  error, the card says so in plain words.
- No new Python, no change to `latest.json`; the service worker does not cache the photos.

## Consequences
- It works on GitHub Pages without a server, and costs one STAC search plus a few range reads per
  press. It depends on Planetary Computer's availability.
- 10 m pixels: a 4 ha field is about 20 × 20 pixels, so the photo shows patches, not plants.
- Offline, the button shows the error text.
