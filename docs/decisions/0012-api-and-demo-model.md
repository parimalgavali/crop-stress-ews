# 0012 — API over precomputed predictions; demo served by the calibrated logistic model

Status: Accepted (2026-10-27). Uses [0008](0008-evaluation-protocol.md), [0010](0010-peer-reference-label.md), [0011](0011-sequence-models.md).

## Context

US-10 needs one backend for the UI and the replay demo: fields on a map and, per field and date,
7/14/21-day risk with a short reason a non-expert can understand.

## Decision

- **Precomputed, not live inference.** `scripts/export_predictions.py` scores the test (2024) and
  extra-check (2025) seasons once; `scripts/load_db.py` loads them into PostGIS. The API only reads.
- **Demo model: US-08 logistic regression, Platt-calibrated on validation.** On Soest it is within
  the CIs of LightGBM and the sequence models, and its per-feature contributions
  (coefficient × standardised value) give reasons that are faithful to the score, not a separate
  post-hoc explainer. Contributions are summed into ~10 plain-language groups (EN/DE), top 2 shown.
- **Traffic light:** red ≥ threshold at 90% validation specificity (the ADR 0008 alarm threshold),
  amber ≥ 75% validation specificity, else green.
- Rows are exported only where the horizon ends by the 30 June senescence cutoff, i.e. where the
  label is defined.
- **Stack:** FastAPI + SQLAlchemy 2 + GeoAlchemy2 + Alembic on PostGIS 16, `docker compose up`.
  Optional `api` extra. API tests run against a PostGIS service container in CI.

## Consequences

- Swapping in a better model later only changes the export script.
- The demo shows exactly the evaluated predictions; nothing is tuned on test.
