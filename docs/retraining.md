# Yearly retraining (US-28, ADR 0026, Issue #63)

Code: `src/cropews/retrain.py`, `scripts/retrain.py`. `scripts/export_live_model.py` uses the same
`fit_bundle`. The refactor reproduces the published `risk-v1` model exactly (same coefficients and
red/amber thresholds at all three horizons).

## Rule
- The challenger uses the US-08 train seasons plus `--add`. It is calibrated on the 2022 validation
  season, like the champion.
- Both models are scored on `--holdout`, a season neither has seen.
- Promote only if the mean AUROC over 7/14/21 days improves and no horizon loses more than 0.01
  (`MAX_HORIZON_DROP`). Otherwise the challenger isn't written.

## Backtest: what retraining in autumn 2024 would have done
Holdout 2025, `--add 2024`:

| Horizon | Champion (risk-v1) | Challenger (+2024) | Δ |
|---|---:|---:|---:|
| 7 d | 0.873 | 0.862 | −0.011 |
| 14 d | 0.886 | 0.875 | −0.011 |
| 21 d | 0.875 | 0.863 | −0.012 |

**Not promoted.** Adding the very wet 2024 season made 2025 slightly worse. More data is not
automatically better, which is why the gate exists.

## Yearly steps (next: harvest 2026, from autumn 2026)
1. **Labels:** the current LWK parcel file (`VALIDFROM` 2026) already holds the harvest-2026
   declarations, including 68,469 `Winterweichweizen` parcels in NRW. So 2026 doesn't have to wait
   for Europe-LAND, but it needs a mapping from `CODE_TXT` to the Europe-LAND/HCAT parcel table
   first.
2. Extract S2/S1/weather for 2026, then build the grid and labels (README "pipeline").
3. Add 2026 to `SEASONS`, then run `python scripts/retrain.py --holdout 2026 --add 2024 2025`.
4. If promoted: publish `risk_live_challenger.joblib` as `risk_live.joblib` in a new `risk-vN`
   pre-release, update `models.sha256` and the release tag in `pages.yml`, and record the report in
   the PR.
5. Then 2026 joins training, and the next season is the holdout.
