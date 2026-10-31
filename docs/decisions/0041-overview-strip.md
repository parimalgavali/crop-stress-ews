# ADR 0041: "Fields needing a look" overview strip on the Live map

Status: Accepted (US-44, Issue #95)

## Context
EOSDA/OneSoil dashboards lead with "how many fields need attention". Our Live
view made the reader click fields one by one to learn that.

## Decision
- A thin strip under the header, only on the Live tab and only once spring risk
  data exists (`live.risk` non-empty): "N need a look · M keep watching · K look
  fine", counting each monitored field by its worst horizon light.
- A button opens the card of the field needing it most (worst light, then
  highest risk).
- Fields without a traffic light are excluded, and the strip says so — before
  5 April and for fields without risk data, counting them as green would lie.
- No per-district breakdown: the share-of-stressed-fields metric was tested and
  has no yield skill (Issue #58); counts are a navigation aid, not a statistic.

## Consequences
- `overviewCounts`/`worstFieldId`/`worstLevel` in `web/src/live.ts`;
  `LiveCard`'s inline worst-light fold now reuses `worstLevel`.
