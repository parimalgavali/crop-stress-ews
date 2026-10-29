"""DWD ICON weather forecasts via Open-Meteo (CC BY 4.0), live and archived (ADR 0019).

Archived runs with lead time (Previous Runs API) exist from February 2024 only.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
MODEL = "icon_seamless"
LEAD_DAYS = 5
TIMEZONE = "Europe/Berlin"


def _get(url: str, params: dict[str, Any]) -> dict[str, Any]:
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    body = resp.json()
    if isinstance(body, dict) and body.get("error"):
        raise RuntimeError(body.get("reason"))
    return body


def live_forecast(lat: float, lon: float, days: int = 7) -> pd.DataFrame:
    """Daily forecast (date, pr_mm, tasmin_c, tasmax_c) from today's ICON run."""
    body = _get(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum,temperature_2m_min,temperature_2m_max",
            "models": MODEL,
            "forecast_days": days + 1,
            "timezone": TIMEZONE,
        },
    )
    d = body["daily"]
    return pd.DataFrame(
        {
            "date": pd.to_datetime(d["time"]),
            "pr_mm": d["precipitation_sum"],
            "tasmin_c": d["temperature_2m_min"],
            "tasmax_c": d["temperature_2m_max"],
        }
    ).dropna()


def archived_forecast(
    lat: float, lon: float, start: date, end: date, leads: int = LEAD_DAYS
) -> pd.DataFrame:
    """Daily (date, lead, pr_mm, tasmin_c): forecast for ``date`` issued ``lead`` days before."""
    hourly = [
        f"{v}_previous_day{k}"
        for k in range(1, leads + 1)
        for v in ("precipitation", "temperature_2m")
    ]
    body = _get(
        PREVIOUS_RUNS_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": ",".join(hourly),
            "models": MODEL,
            "timezone": TIMEZONE,
        },
    )
    h = pd.DataFrame(body["hourly"])
    h["date"] = pd.to_datetime(h.pop("time")).dt.normalize()
    rows = []
    for k in range(1, leads + 1):
        day = h.groupby("date").agg(
            pr_mm=(f"precipitation_previous_day{k}", lambda s: s.sum(min_count=24)),
            tasmin_c=(
                f"temperature_2m_previous_day{k}",
                lambda s: s.min() if s.notna().all() else None,
            ),
        )
        rows.append(day.assign(lead=k).reset_index())
    return pd.concat(rows, ignore_index=True)


def issued_features(archive: pd.DataFrame, leads: int = LEAD_DAYS) -> pd.DataFrame:
    """Per issue date: forecast rain sum and min temperature over the next ``leads`` days."""
    a = archive[archive["lead"] <= leads]
    a = a.assign(issued=a["date"] - pd.to_timedelta(a["lead"], unit="D"))
    out = a.groupby("issued").agg(
        fc_rain_5d=("pr_mm", "sum"), fc_tmin_5d=("tasmin_c", "min"), n=("pr_mm", "count")
    )
    out = out[out["n"] == leads].drop(columns="n")
    return out.reset_index().rename(columns={"issued": "date"})


def observed_features(daily: pd.DataFrame, leads: int = LEAD_DAYS) -> pd.DataFrame:
    """Per field and date: the same window from observed daily weather (a perfect forecast)."""
    d = daily.assign(date=pd.to_datetime(daily["date"]))
    d = d.sort_values(["field_id", "date"]).reset_index(drop=True)
    g = d.groupby("field_id")
    out = d[["field_id", "date"]].assign(
        fc_rain_5d=g["pr_mm"].transform(lambda x: x.rolling(leads).sum().shift(-leads)),
        fc_tmin_5d=g["tasmin_c"].transform(lambda x: x.rolling(leads).min().shift(-leads)),
        span=g["date"].transform(lambda x: (x.shift(-leads) - x).dt.days),
    )
    return out[out["span"] == leads].drop(columns="span").reset_index(drop=True)


ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
SOIL_VARS = {"soil_moisture_0_to_7cm_mean": "sm_top", "soil_moisture_7_to_28cm_mean": "sm_root"}


def _soil_frame(body: dict[str, Any]) -> pd.DataFrame:
    d = body["daily"]
    out = pd.DataFrame({"date": pd.to_datetime(d["time"])})
    for k, v in SOIL_VARS.items():
        out[v] = d[k]
    return out.dropna()


def live_soil_moisture(lat: float, lon: float, days: int = 7) -> pd.DataFrame:
    """Daily volumetric soil moisture (m³/m³) at 0–7 and 7–28 cm, today's forecast (ADR 0031)."""
    params = {"latitude": lat, "longitude": lon, "daily": ",".join(SOIL_VARS)}
    return _soil_frame(
        _get(FORECAST_URL, params | {"forecast_days": days + 1, "timezone": TIMEZONE})
    )


def archived_soil_moisture(lat: float, lon: float, start: date, end: date) -> pd.DataFrame:
    """ERA5 reanalysis soil moisture, same columns as ``live_soil_moisture`` (ADR 0031)."""
    params = {"latitude": lat, "longitude": lon, "daily": ",".join(SOIL_VARS)}
    return _soil_frame(
        _get(
            ARCHIVE_URL,
            params
            | {"start_date": start.isoformat(), "end_date": end.isoformat(), "timezone": TIMEZONE},
        )
    )


def soil_moisture_features(daily: pd.DataFrame, leads: int = LEAD_DAYS) -> pd.DataFrame:
    """Per date: soil moisture now and the change expected over the next ``leads`` days."""
    d = daily.sort_values("date").reset_index(drop=True)
    ahead = d["sm_root"][::-1].rolling(leads, min_periods=leads).mean()[::-1].shift(-1)
    return pd.DataFrame(
        {
            "date": d["date"],
            "sm_top": d["sm_top"],
            "sm_root": d["sm_root"],
            "sm_root_change_5d": ahead - d["sm_root"],
        }
    )
