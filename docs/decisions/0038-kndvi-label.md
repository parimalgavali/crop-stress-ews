# ADR 0038: kNDVI stress labels tested and rejected

Status: Rejected (second-round idea #5)

## Context
kNDVI = tanh(NDVI²) (Camps-Valls et al. 2021) saturates less than NDVI at high
biomass, so peer-departure labels built on it could flag stress more cleanly in
dense wheat.

## Test
`scripts/kndvi_label_eval.py` rebuilds events and onset targets with
`LABEL_INDICES = ("kndvi", "ndmi")` (peer reference, ADR 0010), retrains the
served logistic model, and compares AUROC with the current NDVI labels.
Report: `outputs/kndvi_label_eval.json`.

## Result
Worse on the 2022 validation gate at every horizon and mixed elsewhere:

| horizon | NDVI 2022 | kNDVI 2022 | NDVI 2024 | kNDVI 2024 | NDVI 2025 | kNDVI 2025 |
|---|---|---|---|---|---|---|
| 7 d  | 0.858 | 0.853 | 0.742 | 0.743 | 0.868 | 0.868 |
| 14 d | 0.784 | 0.779 | 0.795 | 0.798 | 0.879 | 0.874 |
| 21 d | 0.758 | 0.753 | 0.768 | 0.756 | 0.868 | 0.856 |

## Consequences
- Labels stay on (ndvi, ndmi). The transform only compresses the top of the
  range; our labels already measure *peer departure*, not absolute greenness,
  so saturation does not bite the same way.
