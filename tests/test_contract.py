import pandas as pd
import pytest

from cropews.data.contract import (
    DataContractError,
    field_errors,
    observation_errors,
    validate_fields,
    validate_observations,
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
