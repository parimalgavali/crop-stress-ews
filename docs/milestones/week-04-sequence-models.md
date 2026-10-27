# Week 4 — Sequence models and ablations (US-09)

## What was done

GRU-D and LSTM over causal windows of the 5-day grid, with observed masks and time gaps, seed
ensembles, validation-only selection, Platt calibration and the ADR 0008 protocol
([ADR 0011](../decisions/0011-sequence-models.md), [results](../sequence_models.md)).

## Why

To show whether explicit handling of irregular satellite observations beats the US-08 feature
models — and to report it honestly if it does not.

## How to verify

`pytest -q tests/test_sequence.py tests/test_seqmodels.py` (causality of windows, gap computation,
masked loss, a learnability check), then `python scripts/train_sequence.py`.

## Result (Soest only)

On par with LightGBM; Sentinel-1 is the most valuable input group. CIs overlap.

## Out of scope / next

Six-district rerun of US-08 and US-09 once Sentinel-1 extraction finishes; then US-10 (API).
