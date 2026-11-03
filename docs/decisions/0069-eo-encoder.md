# ADR 0069: Pretrained EO encoder baseline — bounded check, not run

- Status: rejected, 2026-10-26
- Context: dossier P2 — "pretrained EO encoder, frozen embedding baseline under causal
  inputs". Gated on the sequence-model result (frozen embedding + linear head is a
  strictly weaker learner than a trained sequence model).
- Gate math: the ADR 0067 corrective rerun gives the ceiling — a fully trained GRU-D
  scores 0.833/0.804/0.792 on the 2022 gate, already below LightGBM at every horizon.
  A frozen external embedding cannot exceed that ceiling.
- Input mismatch: available EO encoders (Presto — monthly composites; Prithvi —
  10 m chip multi-temporal; Clay — chips) are trained on regular cadences or spatial
  tiles, not on our causal, irregular 5-day masked windows with district-peer anomaly
  features. Feeding our grid would require re-projection outside the models' training
  distribution, weakening the baseline further.
- Verdict: expected value negative at high compute cost; the gating experiment
  (ADR 0067) already failed. Not run. Revisit if a causal-irregular-grid EO encoder
  appears or if the tabular baseline is ever beaten by a trained sequence model.
