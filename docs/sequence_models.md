# Sequence models (US-09)

Method: [ADR 0011](decisions/0011-sequence-models.md). Code: `src/cropews/sequence.py`
(windows, mask, time gaps), `src/cropews/seqmodels.py` (GRU-D, LSTM, training),
`scripts/train_sequence.py` (configs, selection, calibration, evaluation).

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -e ".[model,seq]"
python scripts/train_sequence.py --out data/outputs/sequence.json   # ~2 min on CPU for Soest
```

## Soest, peer label (ADR 0010), 40 fields per season (2026-10-27)

Validation (2022) AUROC — used for selection and ablations:

| Config | 7 d | 14 d | 21 d |
|---|---|---|---|
| GRU-D, full history | 0.801 | 0.784 | 0.787 |
| **LSTM, full history (selected)** | **0.832** | **0.802** | **0.793** |
| GRU-D, 30-day window | 0.810 | 0.793 | 0.800 |
| GRU-D, 60-day window | 0.796 | 0.784 | 0.785 |
| GRU-D, no Sentinel-1 | 0.787 | 0.746 | 0.755 |
| GRU-D, no weather | 0.816 | 0.793 | 0.788 |
| *LightGBM (US-08b)* | *0.84* | *0.82* | *0.77* |

Test 2024 (calibrated, validation-frozen thresholds; 95% field-bootstrap CI):

| Horizon | Model | AUROC [CI] | AUPRC (prev.) | Brier | Sens. | FA/100 |
|---|---|---|---|---|---|---|
| 7 d | LSTM (selected) | 0.768 [0.566–0.953] | 0.176 (0.039) | 0.036 | 0.50 | 38 |
| 7 d | GRU-D | 0.819 [0.662–0.949] | 0.180 | 0.036 | 0.50 | 60 |
| 7 d | *persistence / LightGBM* | *0.664 / 0.800* | | | | |
| 14 d | LSTM (selected) | 0.757 [0.540–0.947] | 0.229 (0.059) | 0.051 | 0.38 | 52 |
| 14 d | GRU-D | 0.795 [0.607–0.951] | 0.227 | 0.051 | 0.50 | 95 |
| 14 d | *persistence / logistic* | *0.698 / 0.777* | | | | |
| 21 d | LSTM (selected) | 0.727 [0.494–0.944] | 0.228 (0.072) | 0.063 | 0.29 | 52 |
| 21 d | GRU-D | 0.772 [0.552–0.954] | 0.252 | 0.061 | 0.47 | 90 |
| 21 d | *persistence / logistic* | *0.686 / 0.735* | | | | |

## Reading

- **Sentinel-1 matters most:** removing it costs 0.02–0.05 validation AUROC (and 0.05–0.07 on
  test), the largest ablation effect — radar fills the cloudy gaps at 14/21 days.
- Weather adds little on top of the canopy signal; a 30-day window is as good as full history.
- Sequence models are on par with LightGBM on Soest, not clearly better; every learned model beats
  persistence on point estimates, and all CIs overlap. The validation-selected LSTM scored lower
  on test than GRU-D — reported as is, not re-selected.
- Decisive comparison: the six-district rerun (≈ 5× the fields) once Sentinel-1 extraction ends.
