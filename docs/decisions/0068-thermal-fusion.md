# ADR 0068: Thermal fusion bounded check — not viable at needed cadence

- Status: rejected, 2026-10-26
- Context: dossier P2 thermal/sensor fusion — "bounded experiment, check native
  resolution, cloud gaps, coverage, licensing, latency first; Landsat ST is a possible
  research substitute". The checks are the deliverable when they fail.
- Check (Planetary Computer STAC, landsat-c2-l2, NRW bbox 6.0–9.5E × 50.3–52.6N,
  Apr–Jul 2022):
  - 214 L2SP overpasses (Landsat 8+9, ~8-day combined revisit over NRW ≈ 8 WRS frames).
  - 68 scenes with scene cloud cover < 30 % → ~27 overpasses × ~30 % ≈ 8 scenes/field
    in 4 months, before pixel-level cloud masking — about 2 usable observations
    per field per month.
  - Resolution: lwir11 (ST_B10) native 100 m — ~9–10 px/ha, usable for a 4 ha field
    but coarse for sub-field stress.
  - Licensing: USGS public domain — fine. Latency: L2 products lag ~1–3 days — fine.
- Verdict: temporal density (~2 obs/month) is ~10× below the 5-day feature grid; the
  thermal band cannot carry a 7/14/21-day warning input or fusion term. Rejected
  before implementation. MODIS/VIIRS LST (daily, 1 km) is too coarse for field scale;
  ECOSTRESS is episodic. Revisit only if a higher-cadence thermal source opens.
