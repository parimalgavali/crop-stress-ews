# ADR 0047: Rain since 1 October vs a usual season

Status: Accepted (US-50, Issue #107)

## Context
A 30-day rain total doesn't tell whether the season so far is wet or dry.
Growers think in "this autumn is unusually wet".

## Decision
- `season_rain()` fetches ERA5 daily precipitation (Open-Meteo archive,
  CC BY 4.0) at each district centroid, 2019-10-01 → as_of, once per live run.
- Card line: "Since 1 October: X mm — usually L–H mm by now · drier/about
  usual/wetter". L–H is the 25–75th percentile of past seasons' cumulative
  rain at the same day-of-season; the line hides when fewer than 4 past
  seasons are available.
- Display only — never a model input (same rule as the forecast, ADR 0019):
  it's identical for every field in a district.

## Consequences
- One archive request per district per run (~7 yr of daily data each).
