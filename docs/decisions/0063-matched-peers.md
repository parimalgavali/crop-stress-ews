# ADR 0063: Soil-matched peer groups — rejected

- Status: rejected, 2026-10-26
- Context: spec — stage/soil/sowing-aware peers with minimum support, adopted only if
  better on the 2022 validation gate. Hypothesis: comparing a field to peers with
  similar soil (BK50 NFK water-hold class) inside its district sharpens the anomaly.
- Experiment: `scripts/matched_peer_eval.py`. Peer class = district × water-hold class
  (little/medium/lots, NFK cut-offs), min_peers=5 with district-date fallback.
  AUROC (delta vs district peers) on validation 2022:

  | model | 7d | 14d | 21d |
  |---|---|---|---|
  | logistic | 0.858→0.837 | 0.784→0.764 | 0.758→0.740 |
  | lightgbm | 0.878→0.867 | 0.833→0.814 | 0.823→0.801 |

- Result: worse at every horizon for both models. Soil-matched peers shrink the peer
  pool (mean support falls below 5 often → district fallback dominates) without adding
  signal. District peers stay. `build_features(peer_key=...)` remains for future
  peer-group experiments.
