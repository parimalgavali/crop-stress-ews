# ADR 0027: Season greenness chart on Live cards

Status: Accepted (US-30, Issue #67)

## Context
A Live card says in words whether a field is green, getting greener, or behind its neighbours
(ADR 0016). It doesn't show how the field got there, and a reader who can't read well gets
little from the text. The live run already holds every clear Sentinel-2 view since 1 October
(ADR 0025), so the history costs no extra extraction.

## Decision
- `cropews.live.season_series` adds `season` to `latest.json`:
  - `fields`: per field, `[date, NDVI]` on clear views (`clear_fraction ≥ 0.8`) since 1 October;
  - `peers`: per district, the median NDVI of the peer fields on each date with at least 5 clear
    peers (the winter-card minimum, ADR 0016);
  - `peer_kind`: `cereal` when the wheat map is on (peers = fields at P ≥ 0.5, the winter-card
    set), otherwise `all` (every monitored arable field, mixed crops), and the legend says which.
- The card draws a small SVG: the field as a solid line with dots (one per clear image), the
  neighbours dashed. Colour is never the only cue (line style, a text legend), and the chart has
  a one-sentence summary used as its accessible name, shown under it and read aloud. The summary
  says greener / about as green / less green than the neighbours on the last clear image, at the
  same ±0.05 NDVI as the trend line.
- No chart with fewer than 2 clear images.

## Consequences
- Raw NDVI against a raw peer median, not the peer z-score of the winter check; the chart shows
  the data behind the hint, it is not a second test. Before 1 December the peers are mixed crops.
- Risk-level changes are not marked: `latest.json` only holds the current forecast; the history
  is in the forecast log branch (ADR 0020).
- Payload grows by about 28 bytes per clear field view (local run, 60 fields to 28 Oct: 196 views, 5.5 kB; Düren had no date with 5 clear peers at 10 fields per district).
