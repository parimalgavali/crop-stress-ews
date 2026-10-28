# Forecast log: replay check (US-20, ADR 0020)

`scripts/forecast_replay.py` logs the 2025 demo forecasts one run at a time (16 runs, every
5 days from 5 April), scores the log as of three dates and compares with the offline metrics.

| Scored as of | 7 d scored / pending | AUROC | 14 d scored / pending | AUROC | 21 d scored / pending | AUROC |
|---|---|---|---|---|---|---|
| 5 May 2025 | 688 / 2,090 | 0.930 | 642 / 2,090 | 0.935 | 318 / 2,280 | 0.902 |
| 15 May 2025 | 1,014 / 1,710 | 0.899 | 991 / 1,710 | 0.919 | 659 / 1,900 | 0.930 |
| 10 Jul 2025 (all due) | 1,994 / 0 | 0.868 | 2,463 / 0 | 0.879 | 2,392 / 0 | 0.868 |
| Offline | | 0.868 | | 0.879 | | 0.868 |

When all forecasts are due:

| Horizon | Onsets | Red alarm, onset happened | Red alarm, no onset | Onset without red alarm |
|---|---|---|---|---|
| 7 d | 31 | 10 | 122 | 21 |
| 14 d | 53 | 30 | 213 | 23 |
| 21 d | 75 | 44 | 260 | 31 |

- The final scoreboard equals the offline AUROC, so logging and scoring add no mistakes.
- Early scoreboards look better than the season does. They contain only early-season forecasts,
  and onsets are rarer then. A score from the first weeks shouldn't be read as the season's result.
- Red alarms are mostly false. Onsets are rare (≈ 2 %), and the red threshold was set at 90 %
  specificity on 2022. The scoreboard shows these counts as they are.
- Some issued forecasts are never scored: the onset label is undefined when a field is already
  in an event or has no clear image in the window (ADR 0010).
