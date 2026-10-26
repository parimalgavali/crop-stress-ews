# Week 2 — Sentinel-1, weather and the 5-day grid

## What was done

| Story | PR | Output |
|---|---|---|
| US-03 Sentinel-1 RTC backscatter per field | #17 | `scripts/extract_s1.py` → `data/interim/s1/` |
| US-04 Daily DWD weather per field | #18 | `scripts/extract_weather.py` → `data/interim/weather/` |
| US-05 Regular 5-day grid with observed masks | this PR | `scripts/build_grid.py` → `data/processed/` |

## Why

Sentinel-2 alone leaves gaps of ~25 days (median longest gap per field), too long for 14/21-day
warnings. Sentinel-1 sees through cloud, and weather is the main leading signal. The grid puts all
sources on one time axis without hiding missing data (ADRs 0004–0006).

## Results (Soest, 2024, 20 fields ≥ 2 ha)

- Sentinel-1: 621 rows, median 37 acquisition dates per field, median longest gap 9 days.
- Weather: 4,260 field-days; April–July rain 320 mm vs. 392 mm grass ET0 (wet season).
- Grid: 500 rows (25 steps × 20 fields); Sentinel-2 observed in 49% of steps, any satellite source
  in 89%; median days since last observation 3 (S2), 4 (S1 asc), 3 (S1 desc).

## How to run

```bash
KRS=data/raw/vg2500/vg2500/VG2500_KRS.shp
python scripts/extract_s2.py --year 2024 --district Soest --n 20 --districts $KRS
python scripts/extract_s1.py --year 2024 --district Soest --n 20 --districts $KRS
python scripts/extract_weather.py --year 2024 --district Soest --n 20 --districts $KRS
python scripts/build_grid.py --year 2024 --district Soest
pytest -q
```

## Out of scope

Stress labels (US-06), full-season extraction for all core districts and years, features and
models.
