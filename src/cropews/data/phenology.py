"""DWD immediate-reporter phenology: winter-wheat growth stage reported near a point (ADR 0029)."""

from __future__ import annotations

import io
import math
from datetime import date
from typing import Any

import pandas as pd
import requests

BASE = "https://opendata.dwd.de/climate_environment/CDC"
OBS_URL = (
    f"{BASE}/observations_germany/phenology/immediate_reporters/crops/recent/"
    "PH_Sofortmelder_Landwirtschaft_Kulturpflanze_Winterweizen_akt.txt"
)
STATIONS_URL = f"{BASE}/help/PH_Beschreibung_Phaenologie_Stationen_Sofortmelder.txt"
ATTRIBUTION = "Growth stages: DWD Climate Data Center, phenology immediate reporters, CC BY 4.0"
# DWD phase id -> stage key, in crop-cycle order (DWD phase definitions, object 202 Winterweizen).
PHASES = {
    10: "sown",
    12: "emerged",
    15: "stem",
    18: "heading",
    21: "yellow",
    22: "ripe",
    24: "harvest",
}
ORDER = list(PHASES)
RADIUS_KM = 40.0


def _read(text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text), sep=";", dtype=str, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return df.apply(lambda c: c.str.strip()).drop(columns=["eor"], errors="ignore")


def parse_observations(text: str) -> pd.DataFrame:
    df = _read(text)
    return pd.DataFrame(
        {
            "station": df["Stations_id"].astype(int),
            "phase": df["Phase_id"].astype(int),
            "date": pd.to_datetime(df["Eintrittsdatum"], format="%Y%m%d").dt.date,
        }
    )


def parse_stations(text: str) -> pd.DataFrame:
    df = _read(text)
    return pd.DataFrame(
        {
            "station": df["Stations_id"].astype(int),
            "name": df["Stationsname"],
            "lat": df["geograph.Breite"].astype(float),
            "lon": df["geograph.Laenge"].astype(float),
        }
    )


def fetch(timeout: float = 60) -> tuple[pd.DataFrame, pd.DataFrame]:
    def get(url: str) -> str:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.content.decode("latin-1")

    return parse_observations(get(OBS_URL)), parse_stations(get(STATIONS_URL))


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((p2 - p1) / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 12742 * math.asin(math.sqrt(a))


def crop_start(as_of: date) -> date:
    """1 September of the sowing year: earlier reports belong to the previous crop."""
    return date(as_of.year if as_of.month >= 9 else as_of.year - 1, 9, 1)


def nearby_stage(
    obs: pd.DataFrame,
    stations: pd.DataFrame,
    lat: float,
    lon: float,
    as_of: date,
    radius_km: float = RADIUS_KM,
) -> dict[str, Any] | None:
    """Most advanced stage reached by at least half of the observers within ``radius_km``.

    Only reports from ``crop_start(as_of)`` up to ``as_of`` count. ``None`` if no observer nearby
    reported this season.
    """
    o = obs[(obs["date"] >= crop_start(as_of)) & (obs["date"] <= as_of) & obs["phase"].isin(ORDER)]
    st = stations[stations["station"].isin(o["station"])].copy()
    st["km"] = [_km(lat, lon, a, b) for a, b in zip(st["lat"], st["lon"], strict=True)]
    st = st[st["km"] <= radius_km]
    o = o[o["station"].isin(st["station"])]
    if o.empty:
        return None
    reached = o.groupby("station")["phase"].agg(lambda p: max(ORDER.index(x) for x in p))
    n = len(reached)
    stage = max(i for i in range(len(ORDER)) if (reached >= i).sum() * 2 >= n)
    phase = ORDER[stage]
    at = o[o["phase"] == phase]
    return {
        "stage": PHASES[phase],
        "observers": n,
        "at_stage": int((reached >= stage).sum()),
        "first_date": min(at["date"]).isoformat(),
        "radius_km": int(radius_km),
    }
