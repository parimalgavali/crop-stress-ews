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
# Sowing to spring restart, from 1 October of the year before harvest (ADR 0016).
WINTER_WINDOW = ("10-01", "03-31")
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

# NRW crop codes of the LWK arable USE_TXT groups (cropews.data.lwk.ARABLE_USES), so that past
# Europe-LAND parcels match the live LWK population (ADR 0018).
ARABLE_CROP_CODES = frozenset(
    {
        "112",
        "114",
        "115",
        "116",
        "118",
        "119",
        "120",
        "121",
        "122",
        "125",
        "131",
        "132",
        "142",
        "143",
        "144",
        "156",
        "157",
        "171",
        "181",
        "182",
        "183",
        "186",
        "187",
        "189",
        "210",
        "211",
        "212",
        "220",
        "221",
        "222",
        "230",
        "240",
        "250",
        "311",
        "312",
        "315",
        "316",
        "320",
        "330",
        "341",
        "393",
        "411",
        "413",
        "414",
        "421",
        "422",
        "423",
        "424",
        "425",
        "427",
        "429",
        "430",
        "432",
        "433",
        "602",
        "603",
        "604",
        "611",
        "613",
        "614",
        "616",
        "618",
        "619",
        "620",
        "622",
        "623",
        "624",
        "627",
        "628",
        "629",
        "630",
        "631",
        "633",
        "634",
        "635",
        "636",
        "637",
        "638",
        "639",
        "640",
        "641",
        "642",
        "643",
        "644",
        "645",
        "646",
        "647",
        "648",
        "649",
        "802",
        "803",
        "804",
        "806",
        "852",
        "853",
        "854",
    }
)
