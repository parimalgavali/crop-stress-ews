# 0009 — Label sanity outcome: keep the label for now, revise before sequence models

Status: Accepted (2026-10-27)

## Context

ADR 0007 required the stress label to pass a check against official district yields (US-07).
Results are in [label_sanity.md](../label_sanity.md): event share tracks yield loss within a
season (Spearman −0.46, p 0.003, 41 district-seasons) but not across seasons (+0.18 overall),
because dry springs (2020, 2022) trigger events that do not cost yield and 2021's late losses are
missed.

## Decision

- Keep ADR 0007's label for the US-08 baselines so protocol and results stay comparable.
- Before US-09, define a revised label as a new ADR, chosen on the validation season only.
  Candidates: per-season peer reference (field vs district median on the same date, removing
  season-wide drought shifts), requiring the anomaly to persist into grain fill (June), or
  combining it with a change-from-own-trajectory condition.
- Report the within-season and across-season correlations for every label variant.

## Consequences

- The project story states honestly that an optical anomaly label is a spatial proxy for yield
  loss, not a season-level one.
- Test season 2024 stays untouched for label selection.
