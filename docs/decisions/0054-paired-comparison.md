# ADR 0054: Model comparisons use a paired field-bootstrap CI of the difference

- Status: accepted, 2026-10-26
- Context: Review finding 4.7 — the existing gate compares overlapping per-model AUROC CIs, which
  is not a direct test of the difference (scores are evaluated on the same fields).
- Decision: `paired_auroc_diff` resamples whole field_ids and reports CI(AUROC_A − AUROC_B) on
  identical rows; `scripts/model_compare.py` runs it per horizon over two score parquets. An
  interval containing 0 means the difference is uncertain — it replaces CI-overlap as the decision
  rule for future challenger checks (e.g. yearly retraining, ADR 0026).
- Note: held-season results already published stay historical development evidence; they were not
  recomputed under this rule and are not described as untouched confirmation.
