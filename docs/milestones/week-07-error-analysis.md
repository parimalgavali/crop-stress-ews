# Week 7 — Error analysis and model card (US-12)

## What was done
- `cropews.errors` and `scripts/error_analysis.py`: red/amber misses and false alarms by district,
  field size and Sentinel-2 cloud gap, plus the lead time of the first alarm before onset.
- [error_analysis.md](../error_analysis.md) (preliminary, Soest 2024) and
  [model_card.md](../model_card.md).
- The replay slider was delivered in US-11.

## Why
To show where the warning fails and how early it fires. Interviewers ask about both.

## How to verify
`pytest -q tests/test_errors.py`. Then run `python scripts/export_predictions.py` followed by
`python scripts/error_analysis.py` on local data.

## Out of scope / next
Six-district rerun once the Sentinel-1 extraction is finished.
