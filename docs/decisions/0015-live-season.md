# 0015 — Live season 2026/27: current conditions for monitored parcels

Status: Accepted (2026-10-27)

## Context

The demo so far replays 2024/2025. Sentinel-1/2 (Planetary Computer) arrive with a lag of about
1–2 days, and DWD HYRAS daily grids with about 1 day (the 2026 file is updated daily). AMBAV
(ET0, soil moisture) is published monthly, so the current month is missing. Europe-LAND
stops at 2025. The NRW Chamber of Agriculture (LWK) publishes the current declared parcels weekly
(`LWK-TSCHLAG`, dl-de/by-2-0, about 743k parcels, `VALIDFROM` 2026).

Which parcels grow winter wheat for **harvest 2027** is only declared in May 2027, and wheat
rarely follows wheat. So the 2026 wheat parcels are the wrong set, and the trained April–July
stress model can't be applied in winter anyway.

## Decision

- **Monitoring set:** a fixed random sample (seed 0) of 30 arable LWK parcels of at least 2 ha per core
  district (180 in total). Arable = `USE_TXT` in Getreide, Ackerfutter, Hackfrüchte, Ölsaaten, Gemüse,
  Eiweißpflanzen or Energiepflanzen. The 2026 declared crop is shown as context.
- **No model scores in winter.** Live mode shows observations only, in plain words: last clear S2
  view and greenness trend, last S1 view and VV change, 30-day rain, and 7-day temperature and frost.
  Stress forecasts start on 5 April 2027, on parcels mapped as winter wheat (US-18).
- **Pipeline:** `scripts/live_update.py` uses a 60-day look-back and writes
  `web/public/live/latest.json` (git-ignored). The Pages workflow runs it every 5 days and on every
  push, then deploys. Nothing is committed to `main`. If the live step fails, the replay demo
  still deploys.

## Consequences

- ~~The sample is redrawn whenever LWK republishes parcels.~~ Amended (US-26, #59): `sample_fields`
  reshuffled the whole sample after small LWK edits (23 → 27 Oct 2026: ~200 of 173,000 parcels
  changed, all 30 Soest and Warendorf fields replaced). Live now uses `stable_sample`: per district
  the n parcels with the smallest sha256 of (season, field_id). Only parcels that disappear drop
  out, and each season (1 Oct) gets a new draw.
- Thresholds in the UI wording (greenness < 0.3 bare, < 0.6 some cover; trend ±0.05; radar
  change ≥ 2 dB) are descriptive, not validated alarms.
