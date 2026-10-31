# ADR 0040: Frost low-spot map — not validatable with open data

Status: Blocked (second-round idea #7, Issue #93)

## Context
A hillshade / cold-air-pocket overlay on the map would flag which monitored fields
sit in frost-collecting low spots. The bar for adding it: a real validation that
the terrain signal predicts frost at field scale.

## Feasibility check
- DEM (Terrarium/Mapzen tiles, ~20 m effective) over the 360 monitored fields:
  real intra-district spread exists — Höxter 108–326 m, Soest 71–390 m,
  Düren 58–368 m — so the terrain signal is there.
- **No open truth at pocket scale:** ICON/ICON-EU (the forecast source) resolves
  ~6.5 km; ERA5-Land 9 km; DWD stations ~20 for all NRW. Cold-air pools form at
  10–100 m scale on clear calm nights — two orders below every available grid.
- No plausible proxy: Sentinel-1 freeze-thaw backscatter is confounded by
  moisture/roughness; Landsat LST (100 m) yields too few clear frost nights per
  winter to test.

## Decision
Not built. A map we cannot test is a claim we cannot defend — same rule that
keeps weather forecast, soil moisture and frost/snow out of the model
(ADR 0019/0030/0031). If a field-scale frost truth appears (e.g. a dense
low-cost sensor network or a validated cold-air-pool model for NRW), revisit.

## Consequences
- Idea closed as blocked; the winter frost *forecast* card (US-38) remains the
  frost product we can verify.
