"""IT.NRW district winter-wheat yields (Landesdatenbank table 41241-03i, dl-de/by-2-0)."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import pandas as pd

YIELD_TABLE_URL = (
    "https://www.landesdatenbank.nrw.de/ldbnrwws/downloader/00/tables/41241-03i_00.csv"
)
CROP_COLUMN = "Winterweizen"


def _number(value: str) -> float:
    try:
        return float(value.replace(",", "."))
    except ValueError:  # "." not available, "/" too uncertain, "-" none
        return float("nan")


def parse_district_yields(source: str | Path) -> pd.DataFrame:
    """District winter-wheat yields in t/ha from the semicolon CSV (Latin-1)."""
    text = Path(source).read_bytes().decode("latin-1") if isinstance(source, Path) else source
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    header = next(r for r in rows if CROP_COLUMN in r)
    col = header.index(CROP_COLUMN)
    records = [
        {
            "year": int(r[0]),
            "ags": r[1],
            "district": r[2].strip().split(",")[0],
            "yield_t_ha": _number(r[col]) / 10,  # dt/ha -> t/ha
        }
        for r in rows
        if len(r) > col and r[0].isdigit() and len(r[1]) == 5
    ]
    return pd.DataFrame(records, columns=["year", "ags", "district", "yield_t_ha"])


def yield_anomaly(yields: pd.DataFrame) -> pd.DataFrame:
    """Relative yield anomaly vs the mean of the district's other years in the table."""
    by = yields.groupby("ags")["yield_t_ha"]
    total, count = by.transform("sum"), by.transform("count")
    others = (total - yields["yield_t_ha"]) / (count - 1).where(count > 1)
    return yields.assign(yield_anomaly=yields["yield_t_ha"] / others - 1)
