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

## Six districts, peer label, 190 fields per season (2026-10-27)

`python scripts/train_sequence.py` (~10 min on CPU). Same configs, seeds and protocol; no retuning.

Validation (2022) AUROC:

| Config | 7 d | 14 d | 21 d |
|---|---|---|---|
| GRU-D, full history | 0.826 | 0.789 | 0.781 |
| LSTM, full history | 0.822 | 0.790 | 0.788 |
| **GRU-D, 30-day window (selected)** | **0.832** | **0.803** | **0.792** |
| GRU-D, 60-day window | 0.824 | 0.790 | 0.782 |
| GRU-D, no Sentinel-1 | 0.830 | 0.791 | 0.784 |
| GRU-D, no weather | 0.825 | 0.788 | 0.777 |

Test 2024 (calibrated, validation-frozen thresholds; 95% field-bootstrap CI):

| Horizon | Model | AUROC [CI] | AUPRC (prev.) | Brier | Sens. | FA/100 |
|---|---|---|---|---|---|---|
| 7 d | GRU-D 30 d (selected) | 0.827 [0.760–0.892] | 0.144 (0.038) | 0.034 | 0.42 | 42 |
| 7 d | LSTM | 0.817 [0.722–0.896] | 0.175 | 0.034 | 0.58 | 56 |
| 7 d | GRU-D, no Sentinel-1 | 0.759 [0.672–0.840] | 0.101 | 0.036 | 0.45 | 56 |
| 7 d | *persistence / logistic / LightGBM* | *0.718 / 0.742 / 0.761* | | | | |
| 14 d | GRU-D 30 d (selected) | 0.809 [0.729–0.888] | 0.176 (0.049) | 0.043 | 0.43 | 64 |
| 14 d | LSTM | 0.800 [0.704–0.879] | 0.221 | 0.043 | 0.49 | 57 |
| 14 d | GRU-D, no Sentinel-1 | 0.749 [0.659–0.834] | 0.122 | 0.045 | 0.47 | 103 |
| 14 d | *persistence / logistic / LightGBM* | *0.722 / 0.795 / 0.792* | | | | |
| 21 d | GRU-D 30 d (selected) | 0.798 [0.708–0.876] | 0.198 (0.059) | 0.051 | 0.47 | 89 |
| 21 d | LSTM | 0.756 [0.650–0.845] | 0.200 | 0.052 | 0.43 | 77 |
| 21 d | GRU-D, no Sentinel-1 | 0.732 [0.630–0.822] | 0.139 | 0.054 | 0.44 | 123 |
| 21 d | *persistence / logistic / LightGBM* | *0.704 / 0.768 / 0.737* | | | | |

### Reading (six districts)

- **Selected model:** GRU-D with a 30-day window has the best test AUROC at every horizon and
  beats persistence by 0.09–0.11, but the CIs still touch or overlap (7 d: [0.760–0.892] vs
  [0.616–0.812]). Not a proven win under ADR 0008.
- **Correction to the Soest reading on Sentinel-1:** on validation, which is what ablations are
  judged on (ADR 0011), removing Sentinel-1 no longer changes AUROC (≤ 0.004). On test it costs
  0.03 AUROC and raises false alarms (descriptive only). So "Sentinel-1 matters most" does not hold
  up on six districts; the honest claim is "helps on test, not shown on validation".
- Removing weather slightly lowers validation AUROC and raises test AUROC; weather adds no robust
  signal for this optical label.
