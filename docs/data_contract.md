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

Downstream code must treat observations with `clear_fraction < 0.8` as missing and carry an
explicit missingness mask.
