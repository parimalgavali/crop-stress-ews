# Field warning follow-up

- Story #167: README, model card and case study now agree on the horizon-aware lead-time
  results (ADR 0050), corrected sequence-model decision (ADR 0067), future paired comparisons
  (ADR 0054), and replay versus Live. Documentation reconciliation; no new evaluation run.

- Story #168: bilingual ntfy copy now names the peer-relative target and inspection next step.
  Alert delivery and episode rules are unchanged.

- Story #169: forecast cards and read-aloud share inspection guidance and distinguish low risk
  from missing forecasts. General observation wording still needs adviser/user review.

- Story #170: evidence quality and clear-image freshness are visible above Live conditions
  and read aloud; missing status is explicitly unknown. No model/threshold changes.

- Story #171: proposed field-trial guide completed, using existing local visit records and
  exports. Recruitment, consent and field observations remain future partner-led work.

- Story #172: regional-warning experiment plan completed, with independent outcomes, baseline
  and future-season gates. No new model, data extraction or claimed validation.

## Validation

- Python: ruff lint/format and mypy pass; pytest 175 passed, 5 skipped (PostGIS unavailable).
  Local environment: Python 3.14 with project extras; the Python 3.10 lock was not reproduced.
- Web: 60 unit tests pass; eslint, TypeScript and production build pass.
- Playwright on macOS: 13 of 14 pass, including all EN/DE axe accessibility checks. The
  keyboard-only test times out before selecting a field; the same test fails identically
  on unchanged main with the same dependencies/browser. No keyboard test changes retained.
- Local links in README, model card, case study and both new guides resolve.
- No field trial, regional experiment, model retraining or alert delivery was performed.
