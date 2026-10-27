# 0005 — Weather: DWD 1 km daily grids (HYRAS + AMBAV) sampled per field

Status: Accepted (2026-10-26)

## Context

Weather is the main leading signal for stress (rain deficit, heat, dry air). ADR 0002 names the
DWD Climate Data Center (CC BY 4.0) as the source. Station data would need interpolation and
station-gap handling; DWD already publishes interpolated 1 km daily grids for Germany.

## Decision

- **HYRAS v6-1** (yearly NetCDF, EPSG:3035, 1 km): precipitation `pr`, mean/min/max air
  temperature `tas`/`tasmin`/`tasmax`, relative humidity `hurs`.
- **AMBAV** (monthly tar of daily ESRI ASCII grids, Gauss-Krüger zone 3 / EPSG:31467, 1 km):
  potential evapotranspiration over grass `evapo_p` (stored in 0.1 mm → `et0_mm`) and soil
  moisture under grass, 60 cm, sandy loam `soil_moist` (% plant-available water → `soil_moist_pct`).
- Each field is sampled at its representative point (fields ≥ 2 ha are much smaller than a 1 km
  cell). `vpd_kpa` is derived with FAO-56 (mean of e°(Tmin), e°(Tmax), times 1 − RH/100).
- The daily window is 1 January – 31 July so that cumulative features have a lead-in before
  predictions start on 1 April.
- Raw files are cached under `data/raw/dwd/` (not committed); ~0.5 GB per season.

## Consequences

- Soil moisture is modelled for grass on a standard soil, not for wheat on the actual soil, so it is
  an indicator of regional water supply, not of a specific field.
- `evapo_p` (AMBAV) is the DWD grass reference evapotranspiration, used as the ET0 proxy instead of
  computing Penman-Monteith from radiation and wind.
- Cite as "DWD Climate Data Center (CDC)" with dataset names; CC BY 4.0.
