# ADR 0029: Nearby winter-wheat growth stage from DWD phenology observers

Status: Accepted (US-32, Issue #71)

## Context
A card that says "less green than the neighbours" means something different at sowing than at
stem elongation. xarvio estimates the growth stage per field with a crop model. We have no
validated stage model, but DWD publishes daily-updated reports from volunteer observers
("Sofortmelder"): sowing, emergence, stem elongation (BBCH 31), heading (BBCH 51), yellow ripeness,
full ripeness and harvest of winter wheat, under CC BY 4.0. On 28 Oct 2026, 24 NRW observers had
reported this autumn, and each core district had 2–4 within 40 km.

## Decision
- `cropews.data.phenology` reads the recent winter-wheat file and the observer list. For each
  district (centroid of its monitored fields), it finds the observers within 40 km that reported
  from 1 September of the sowing year up to `as_of`. The stage shown is the most advanced one
  reached by at least half of them, with that count, the total, and the first date it was
  reported.
- Reports before 1 September belong to the previous crop (for example the August harvest).
- `latest.json.phenology[district]`, and the Live card line: "🌿 Winter wheat around here: came
  up (2 of 3 DWD observers within 40 km, first on 11 October)". It is worded as nearby evidence,
  not as this field's stage.
- If the download fails, the line is left out and the run continues. Not a model input.

## Consequences
- The stage can lag behind: observers report when they see a phase on their reference fields.
- Two to four observers per district is thin, so the line always shows the count.
