import pandas as pd
import pytest

from cropews.data.contract import (
    DataContractError,
    field_errors,
    observation_errors,
    s1_observation_errors,
    validate_fields,
    validate_observations,
    validate_s1_observations,
    validate_weather,
    weather_errors,
)


@pytest.fixture
def fields(raw_parcels):
    return raw_parcels.assign(year=2024, crop_code="115")


@pytest.fixture
def obs():
    return pd.DataFrame(
        {
            "field_id": ["a", "a"],
            "year": [2024, 2024],
            "date": pd.to_datetime(["2024-04-03", "2024-04-08"]).date,
            "coverage": [1.0, 0.95],
            "clear_fraction": [1.0, 0.2],
            "ndvi": [0.8, float("nan")],
            "ndmi": [0.3, 0.1],
            "ndre": [0.4, 0.2],
            "evi": [0.6, 0.5],
            "msi": [0.6, 0.9],
        }
    )


def test_valid_fields_pass(fields):
    assert validate_fields(fields) is fields


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda f: f.drop(columns="field_size"), "missing columns"),
        (lambda f: f.assign(field_id="a"), "duplicate"),
        (lambda f: f.assign(field_size=0.0), "field_size"),
        (lambda f: f.assign(year=2015), "year outside"),
        (lambda f: f.set_crs(None, allow_override=True), "CRS"),
        (lambda f: f.assign(geometry=f.geometry.centroid), "Polygon"),
    ],
)
def test_invalid_fields_are_reported(fields, mutate, message):
    assert any(message in e for e in field_errors(mutate(fields)))
    with pytest.raises(DataContractError):
        validate_fields(mutate(fields))


def test_valid_observations_pass(obs):
    assert observation_errors(obs) == []
    assert validate_observations(obs) is obs


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("clear_fraction", 1.5, "clear_fraction"),
        ("coverage", -0.1, "coverage"),
        ("ndvi", -1.2, "ndvi"),
        ("field_id", "a", None),
    ],
)
def test_invalid_observations_are_reported(obs, column, value, message):
    bad = obs.copy()
    if column == "field_id":
        bad["date"] = bad["date"].iloc[0]
        message = "duplicate"
    else:
        bad.loc[0, column] = value
    assert any(message in e for e in observation_errors(bad))


def _s1_obs(**overrides):
    row = {
        "field_id": "a",
        "year": 2024,
        "date": "2024-05-01",
        "orbit_state": "ascending",
        "relative_orbit": 15,
        "coverage": 1.0,
        "vv_db": -10.0,
        "vh_db": -17.0,
        "vh_vv_db": -7.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_valid_s1_observations_pass():
    assert s1_observation_errors(_s1_obs()) == []


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"orbit_state": "up"}, "orbit_state"),
        ({"coverage": 1.5}, "coverage"),
        ({"vv_db": 0.1 * -32768}, "vv_db"),
    ],
)
def test_invalid_s1_observations(overrides, message):
    errors = s1_observation_errors(_s1_obs(**overrides))
    assert any(message in e for e in errors)


def test_duplicate_s1_rows_rejected():
    obs = pd.concat([_s1_obs(), _s1_obs()])
    with pytest.raises(DataContractError, match="duplicate"):
        validate_s1_observations(obs)


def _weather(**overrides):
    row = {
        "field_id": "a",
        "year": 2024,
        "date": "2024-05-01",
        "pr_mm": 2.0,
        "tas_c": 12.0,
        "tasmin_c": 6.0,
        "tasmax_c": 18.0,
        "hurs_pct": 70.0,
        "vpd_kpa": 0.5,
        "et0_mm": 3.0,
        "soil_moist_pct": 90.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_valid_weather_passes():
    assert weather_errors(_weather()) == []


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"pr_mm": -1.0}, "pr_mm"),
        ({"hurs_pct": 120.0}, "hurs_pct"),
        ({"tasmin_c": 20.0}, "tasmin_c > tasmax_c"),
        ({"et0_mm": float("nan")}, "missing weather"),
    ],
)
def test_invalid_weather(overrides, message):
    assert any(message in e for e in weather_errors(_weather(**overrides)))


def test_duplicate_weather_rows_rejected():
    with pytest.raises(DataContractError, match="duplicate"):
        validate_weather(pd.concat([_weather(), _weather()]))


def test_missing_s1_backscatter_rejected():
    assert "missing backscatter values" in s1_observation_errors(_s1_obs(vv_db=float("nan")))


def test_inconsistent_s1_ratio_rejected():
    obs = _s1_obs()
    obs["vh_vv_db"] += 1.0
    assert "vh_vv_db != vh_db - vv_db" in s1_observation_errors(obs)
