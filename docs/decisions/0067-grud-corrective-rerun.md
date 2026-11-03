# ADR 0067: GRU-D corrective rerun — still below the baseline gate

- Status: accepted, 2026-10-26
- Context: ADR 0049 found the GRU-D input decay was dead at zero init; all sequence
  numbers predating the fix were marked superseded. `train_sequence.py` was rerun with
  w_x/b_x = 0.1/0.01.
- Result (validation 2022 AUROC, the ADR 0008 gate):

  | model | 7d | 14d | 21d |
  |---|---|---|---|
  | GRU-D (selected, 30-day window) | 0.833 | 0.804 | 0.792 |
  | GRU-D | 0.830 | 0.797 | 0.788 |
  | LSTM | 0.822 | 0.790 | 0.788 |
  | LightGBM baseline | 0.878 | 0.833 | 0.823 |
  | Logistic baseline | 0.858 | 0.784 | 0.758 |

  Test 2024 (selected): 0.827 / 0.810 / 0.799. Extra check 2025: 0.902 / 0.891 / 0.834.
- Decision: not adopted. The tabular baselines beat the best sequence model at every
  horizon on the gate season. Sequence models stay a research comparison; the served
  model and baselines are unchanged. The pre-fix "GRU-D wins" claim in README /
  sequence_models is superseded by these numbers.
