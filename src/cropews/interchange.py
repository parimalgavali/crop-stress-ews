"""Versioned import/export contract for field boundaries, risk scores and observations.

Dossier item 6.4 / P2 "Data import/export contract": a documented GeoJSON/CSV
interchange with explicit coordinate reference system, units and model-version
metadata, plus a clearly labelled simulated external adapter.

Contract versions: fields v1, scores v1, observations v1 (mirrors the web app's
`cropews.observations.v1` export envelope).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

CONTRACT_VERSION = 1
REQUIRED_CRS = "EPSG:4326"

OBSERVER_TYPES = ("farmer", "agronomist", "developer", "other")
SYMPTOMS = (
    "none_seen",
    "patchy_growth",
    "yellowing",
    "wilting",
    "standing_water",
    "bare_soil",
    "lodging",
    "other",
)
SEVERITIES = ("mild", "moderate", "severe")
CAUSES = (
    "unknown",
    "water",
    "frost",
    "heat",
    "pest_disease",
    "nutrition",
    "mechanical",
    "not_stress",
)
REVIEW_STATUSES = ("unreviewed", "reviewed")

SCORE_COLUMNS = (
    "field_id",
    "date",
    "horizon_days",
    "risk",
    "level",
    "model_version",
    "issued_at",
    "feature_cutoff",
)


class ContractError(ValueError):
    """Raised when an imported document violates the interchange contract."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def export_fields_geojson(fields: pd.DataFrame) -> str:
    """FeatureCollection export. Required columns: field_id, geometry.

    Optional: district, crop, area_ha. `geometry` holds GeoJSON geometry dicts.
    """
    features = []
    for _, row in fields.iterrows():
        props = {
            "field_id": str(row["field_id"]),
            "district": row.get("district"),
            "crop": row.get("crop"),
            "area_ha": float(row["area_ha"]) if pd.notna(row.get("area_ha")) else None,
        }
        features.append(
            {
                "type": "Feature",
                "properties": {k: v for k, v in props.items() if v is not None},
                "geometry": row["geometry"],
            }
        )
    doc = {
        "type": "FeatureCollection",
        "contract": "cropews-fields",
        "contract_version": CONTRACT_VERSION,
        "crs": {"type": "name", "properties": {"name": f"urn:ogc:def:crs:{REQUIRED_CRS}"}},
        "units": {"area_ha": "hectare"},
        "produced_at": _now(),
        "features": features,
    }
    return json.dumps(doc)


def import_fields_geojson(text: str) -> pd.DataFrame:
    """Validate and parse a cropews-fields document into a DataFrame."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(f"not valid JSON: {exc}") from exc
    if doc.get("contract") != "cropews-fields":
        raise ContractError("missing or wrong 'contract' marker")
    if doc.get("contract_version") != CONTRACT_VERSION:
        raise ContractError(f"unsupported contract_version {doc.get('contract_version')}")
    crs = (doc.get("crs") or {}).get("properties", {}).get("name", "")
    if REQUIRED_CRS not in crs:
        raise ContractError(f"CRS must be {REQUIRED_CRS}, got {crs!r}")
    rows = []
    for i, feat in enumerate(doc.get("features", [])):
        props = feat.get("properties", {})
        geom = feat.get("geometry") or {}
        if not props.get("field_id"):
            raise ContractError(f"feature {i}: field_id missing")
        if geom.get("type") not in ("Polygon", "MultiPolygon"):
            raise ContractError(f"feature {i}: geometry must be Polygon or MultiPolygon")
        rows.append(
            {
                "field_id": str(props["field_id"]),
                "district": props.get("district"),
                "crop": props.get("crop"),
                "area_ha": props.get("area_ha"),
                "geometry": geom,
            }
        )
    return pd.DataFrame(rows)


def export_scores_csv(scores: pd.DataFrame) -> str:
    """CSV export with a contract directive line (risk is a unitless 0..1 score)."""
    missing = set(SCORE_COLUMNS) - set(scores.columns)
    if missing:
        raise ContractError(f"scores frame lacks required columns: {sorted(missing)}")
    header = "# contract=cropews-scores version=1 units=risk:0..1,horizon_days:days date:ISO-8601\n"
    return header + scores[list(SCORE_COLUMNS)].to_csv(index=False)


def import_scores_csv(text: str) -> pd.DataFrame:
    """Validate and parse a cropews-scores CSV (directives + blank lines skipped)."""
    lines = text.splitlines()
    if not lines or "contract=cropews-scores" not in lines[0]:
        raise ContractError("first line must be the contract directive")
    if "version=1" not in lines[0]:
        raise ContractError("unsupported contract version")
    body = "\n".join(x for x in lines[1:] if not x.startswith("#") and x.strip())
    from io import StringIO

    df = pd.read_csv(StringIO(body))
    missing = set(SCORE_COLUMNS) - set(df.columns)
    if missing:
        raise ContractError(f"required columns missing: {sorted(missing)}")
    if df["risk"].isna().any() or not df["risk"].between(0, 1).all():
        raise ContractError("risk must be a number between 0 and 1")
    if df["issued_at"].isna().any() or df["feature_cutoff"].isna().any():
        raise ContractError("issued_at and feature_cutoff are required on every row")
    return df


def import_observations(text: str) -> pd.DataFrame:
    """Validate a cropews-observations export (envelope or bare record list).

    Mirrors `web/src/observations.ts` schema_version 1: field_id, observed_at,
    observer_type, symptom, severity|null, suspected_cause, review_status.
    """
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(f"not valid JSON: {exc}") from exc
    if isinstance(doc, dict):
        if doc.get("schema_version") != CONTRACT_VERSION:
            raise ContractError(f"unsupported schema_version {doc.get('schema_version')}")
        records = doc.get("records")
    else:
        records = doc
    if not isinstance(records, list):
        raise ContractError("records must be a list")
    rows = []
    for i, rec in enumerate(records):
        fid = rec.get("field_id")
        if not fid:
            raise ContractError(f"record {i}: field_id missing")
        try:
            datetime.fromisoformat(str(rec.get("observed_at", "")).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractError(f"record {i}: observed_at not ISO-8601") from exc
        if rec.get("observer_type") not in OBSERVER_TYPES:
            raise ContractError(f"record {i}: bad observer_type {rec.get('observer_type')!r}")
        if rec.get("symptom") not in SYMPTOMS:
            raise ContractError(f"record {i}: bad symptom {rec.get('symptom')!r}")
        sev = rec.get("severity")
        if sev is not None and sev not in SEVERITIES:
            raise ContractError(f"record {i}: bad severity {sev!r}")
        if rec.get("suspected_cause") not in CAUSES:
            raise ContractError(f"record {i}: bad suspected_cause {rec.get('suspected_cause')!r}")
        if rec.get("review_status", "unreviewed") not in REVIEW_STATUSES:
            raise ContractError(f"record {i}: bad review_status")
        rows.append(dict(rec))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- simulated adapter
# Clearly labelled simulated adapter (dossier 6.4): a hypothetical partner export
# ("AgriConnect-style") uses different property names and no contract metadata.
# The adapter maps it into the cropews-fields contract. A real adapter would also
# reproject coordinates; this one only maps the schema.

SIMULATED_ADAPTER = "agriconnect-simulated-v1"


def adapt_simulated_export(text: str) -> str:
    """Map a simulated foreign FeatureCollection into cropews-fields JSON."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(f"not valid JSON: {exc}") from exc
    if doc.get("adapter") != SIMULATED_ADAPTER:
        raise ContractError(f"expected adapter marker {SIMULATED_ADAPTER!r}")
    rows = []
    for i, feat in enumerate(doc.get("features", [])):
        props = feat.get("properties", {})
        if not props.get("feldname"):
            raise ContractError(f"feature {i}: feldname missing")
        rows.append(
            {
                "field_id": props["feldname"],
                "district": props.get("kreis"),
                "crop": props.get("frucht"),
                "area_ha": props.get("flaeche_ha"),
                "geometry": feat.get("geometry"),
            }
        )
    out = json.loads(export_fields_geojson(pd.DataFrame(rows)))
    out["adapted_from"] = SIMULATED_ADAPTER
    return json.dumps(out)
