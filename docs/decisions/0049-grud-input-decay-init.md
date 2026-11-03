# ADR 0049: GRU-D input decay starts with positive rates

- Status: accepted, 2026-10-26
- Context: External review finding 4.1 (research dossier, 3 Nov 2026) showed `w_x`/`b_x`
  zero-initialised in `src/cropews/seqmodels.py` sit on ReLU's kink at every time step, so the
  input-decay branch gets zero gradient and can never learn. Only hidden-state decay worked.
- Decision: initialise `w_x = 0.1`, `b_x = 0.01` (positive), so every time gap `d > 0` yields a
  nonzero gradient. Hidden-state decay (`decay_h` Linear layer) is untouched.
- Consequences: GRU-D published scores are not valid "learned input decay"; historical runs used a
  degenerate decay (gamma = 1, missing inputs carried last observation unchanged). Headline
  model selection is unaffected in kind but rerun numbers should be recomputed in a corrective
  release before new claims are made (dossier roadmap week 1-2). Regression tests pin gradient
  flow, monotonic decay with gap, and that observed inputs pass through unaltered.
