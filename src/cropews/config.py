"""Project-wide constants. Rationale lives in docs/decisions/."""

from __future__ import annotations

WORKING_CRS = "EPSG:25832"

WINTER_WHEAT_HCAT = "winter_common_soft_wheat"
NRW_WINTER_WHEAT_CROP_CODE = "115"

SEASONS: tuple[int, ...] = tuple(range(2019, 2026))
SPLITS: dict[str, tuple[int, ...]] = {
    "train": (2019, 2020, 2021, 2023),
    "validation": (2022,),
    "test": (2024,),
    "extra_check": (2025,),
}

PREDICTION_WINDOW = ("04-01", "07-31")
HORIZONS_DAYS: tuple[int, ...] = (7, 14, 21)

CORE_DISTRICTS: tuple[str, ...] = (
    "Soest",
    "Warendorf",
    "Höxter",
    "Coesfeld",
    "Düren",
    "Rhein-Erft-Kreis",
)

EUROPE_LAND_NRW_URL = (
    "https://zenodo.org/api/records/18670815/files/DE_NRW_years_2019-2025.zip/content"
)
EUROPE_LAND_MEMBER = "GSA-DE_NRW-{year}.geoparquet"
