# Data contract

Implemented in `src/cropews/data/contract.py`; violations raise `DataContractError`.

## Fields (one row per parcel and season)

| Column | Type | Rule |
|---|---|---|
| `field_id` | str | Unique per `year` |
| `year` | int | 2019–2025 |
| `crop_code` | str | Original state code (`115` = winter soft wheat in NRW) |
| `EC_hcat_n` | str | HCAT name (`winter_common_soft_wheat`) |
| `field_size` | float | Hectares, > 0 |
| `geometry` | polygon | Polygon or MultiPolygon, non-empty; CRS set (working CRS EPSG:25832) |

## Sentinel-2 observations (one row per field and acquisition date)

| Column | Type | Rule |
|---|---|---|
| `field_id`, `year` | | Join keys to fields; (`field_id`, `date`) unique (overlapping tiles: clearest scene kept) |
| `date` | date | Acquisition date (UTC) |
| `coverage` | float | Share of the (buffered) field's pixels with data in this scene, in [0, 1]; rows below 0.9 are dropped |
| `clear_fraction` | float | Share of valid pixels with SCL 4/5, in [0, 1] |
| `ndvi`, `ndmi`, `ndre` | float | Median over clear pixels, in [-1, 1] or NaN if no clear pixels |
| `evi`, `msi` | float | Median over clear pixels, or NaN |

## Sentinel-1 observations (one row per field, acquisition date and orbit direction)

| Column | Type | Rule |
|---|---|---|
| `field_id`, `year`, `date` | | (`field_id`, `date`, `orbit_state`) unique (overlapping slices: best coverage kept) |
| `orbit_state` | str | `ascending` or `descending` |
| `relative_orbit` | int | Sentinel-1 relative orbit number |
| `coverage` | float | Share of field pixels valid in VV and VH, in [0, 1]; rows below 0.9 are dropped |
| `vv_db`, `vh_db` | float | Median gamma0 in dB, within [−40, 10] |
| `vh_vv_db` | float | `vh_db − vv_db` |

## Weather (one row per field and day, 1 January – 31 July)

| Column | Type | Rule |
|---|---|---|
| `field_id`, `year`, `date` | | (`field_id`, `date`) unique; no missing values |
| `pr_mm` | float | Daily precipitation (HYRAS), ≥ 0 |
| `tas_c`, `tasmin_c`, `tasmax_c` | float | Daily mean/min/max air temperature (HYRAS); `tasmin_c` ≤ `tasmax_c` |
| `hurs_pct` | float | Daily mean relative humidity (HYRAS), in [0, 100] |
| `vpd_kpa` | float | FAO-56 vapour-pressure deficit, ≥ 0 |
| `et0_mm` | float | Potential evapotranspiration over grass (AMBAV `evapo_p`), ≥ 0 |
| `soil_moist_pct` | float | Soil moisture under grass, % plant-available water (AMBAV), ≥ 0 |

Downstream code must treat Sentinel-2 observations with `clear_fraction < 0.8` as missing and carry an
explicit missingness mask.

## 5-day grid (one row per field and grid date t; step is (t − 5 d, t])

| Column | Rule |
|---|---|
| `field_id`, `year`, `date` | (`field_id`, `date`) unique; dates every 5 days from 5 April |
| `ndvi` … `msi` | Latest clear Sentinel-2 value in the step, else NaN (never forward-filled) |
| `vv_db_asc` … `vh_vv_db_desc` | Latest Sentinel-1 value per orbit direction in the step, else NaN |
| `s2_observed`, `s1_asc_observed`, `s1_desc_observed` | True iff the source has a value in the step |
| `*_days_since` | Days since latest observation on or before t (< 5 when observed; NaN if none yet) |
| weather columns | Step sums (`pr_mm`, `et0_mm`), means, min/max, last `soil_moist_pct`; `weather_observed` = 5 days present |
