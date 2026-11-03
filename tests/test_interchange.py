import json
from pathlib import Path

import pandas as pd
import pytest

from cropews.interchange import (
    SCORE_COLUMNS,
    ContractError,
    adapt_simulated_export,
    export_fields_geojson,
    export_scores_csv,
    import_fields_geojson,
    import_observations,
    import_scores_csv,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _fields_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "field_id": ["f1"],
            "district": ["Soest"],
            "crop": ["Winterweizen"],
            "area_ha": [4.2],
            "geometry": [
                {
                    "type": "Polygon",
                    "coordinates": [[[8.0, 51.5], [8.01, 51.5], [8.01, 51.49], [8.0, 51.5]]],
                }
            ],
        }
    )


def test_fields_geojson_round_trip() -> None:
    text = export_fields_geojson(_fields_frame())
    back = import_fields_geojson(text)
    assert list(back["field_id"]) == ["f1"]
    assert back.loc[0, "area_ha"] == 4.2


def test_fields_import_rejects_wrong_contract() -> None:
    with pytest.raises(ContractError, match="contract"):
        import_fields_geojson('{"type": "FeatureCollection", "features": []}')


def test_fields_import_rejects_wrong_crs() -> None:
    doc = json.loads(export_fields_geojson(_fields_frame()))
    doc["crs"]["properties"]["name"] = "urn:ogc:def:crs:EPSG:25832"
    with pytest.raises(ContractError, match="EPSG:4326"):
        import_fields_geojson(json.dumps(doc))


def test_scores_csv_round_trip() -> None:
    df = pd.DataFrame({c: ["f1", "f1"] for c in SCORE_COLUMNS})
    df["risk"] = [0.4, 0.7]
    df["horizon_days"] = [7, 7]
    text = export_scores_csv(df)
    back = import_scores_csv(text)
    assert len(back) == 2 and back["risk"].max() == 0.7


def test_scores_import_rejects_bad_risk() -> None:
    bad = (
        "# contract=cropews-scores version=1\n"
        "field_id,date,horizon_days,risk,level,model_version,issued_at,feature_cutoff\n"
        "f1,2027-04-05,7,1.4,red,v1,2027-04-05T06:00Z,2027-04-04\n"
    )
    with pytest.raises(ContractError, match="risk"):
        import_scores_csv(bad)


def test_scores_import_rejects_missing_directive() -> None:
    with pytest.raises(ContractError, match="directive"):
        import_scores_csv("field_id,risk\nf1,0.5\n")


def test_observations_envelope_import() -> None:
    envelope = {
        "schema_version": 1,
        "exported_at": "2027-05-01T10:00:00Z",
        "records": [
            {
                "field_id": "f1",
                "observed_at": "2027-04-30",
                "observer_type": "farmer",
                "symptom": "wilting",
                "severity": "moderate",
                "suspected_cause": "water",
                "review_status": "unreviewed",
            }
        ],
    }
    df = import_observations(json.dumps(envelope))
    assert len(df) == 1 and df.loc[0, "symptom"] == "wilting"


def test_observations_reject_unknown_cause() -> None:
    bad = [
        {
            "field_id": "f1",
            "observed_at": "2027-04-30",
            "observer_type": "farmer",
            "symptom": "wilting",
            "severity": None,
            "suspected_cause": "aliens",
            "review_status": "unreviewed",
        }
    ]
    with pytest.raises(ContractError, match="suspected_cause"):
        import_observations(json.dumps(bad))


def test_observations_reject_old_schema() -> None:
    with pytest.raises(ContractError, match="schema_version"):
        import_observations(json.dumps({"schema_version": 0, "records": []}))


def test_simulated_adapter_maps_and_validates() -> None:
    foreign = (FIXTURES / "adapter_demo" / "simulated_fields.json").read_text()
    adapted = adapt_simulated_export(foreign)
    df = import_fields_geojson(adapted)  # output passes our own contract
    assert list(df["field_id"]) == ["K0347", "K0348"]
    assert df.loc[0, "district"] == "Soest"
    assert json.loads(adapted)["adapted_from"] == "agriconnect-simulated-v1"


def test_simulated_adapter_rejects_unmarked_doc() -> None:
    with pytest.raises(ContractError, match="adapter"):
        adapt_simulated_export('{"type": "FeatureCollection", "features": []}')
