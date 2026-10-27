# Error analysis — test season 2024 (US-12)

`python scripts/error_analysis.py [--level red|amber]` joins the exported traffic lights
(`data/outputs/predictions.parquet`, [ADR 0012](decisions/0012-api-and-demo-model.md)) to the
labels, the field size and the Sentinel-2 cloud gap (`s2_days_since`, the number of days since the
last clear optical image). Code: `cropews.errors`.

**Scope: six core districts, 190 test field-seasons (2026-10-27).** The first pass was Soest only
(40 field-seasons: red alarms before 6 of 9 onsets, median 17.5 days). With 0–43 events per cell,
treat per-district numbers as indicative.

## Red alarms (90% validation specificity)

| Horizon | Events | Sensitivity | False alarms / 100 fields | Precision |
|---|---|---|---|---|
| 7 d | 38 | 0.32 | 35 | 0.15 |
| 14 d | 75 | 0.31 | 39 | 0.23 |
| 21 d | 106 | 0.36 | 71 | 0.22 |

The counts are per field-season over the whole season. One field can raise several alarms.

**By district, 14 d:**

| District | Events | Sensitivity | False alarms / 100 fields |
|---|---|---|---|
| Soest | 26 | 0.38 | 40 |
| Warendorf | 29 | 0.28 | 50 |
| Höxter | 10 | 0.40 | 43 |
| Rhein-Erft-Kreis | 8 | 0.13 | 23 |
| Coesfeld | 2 | 0.00 | 77 |
| Düren | 0 | – | 3 |

Coesfeld raises many alarms with almost no events; Düren had no onsets in 2024. A per-district
threshold would help, but it would have to be chosen on validation, not on these numbers.

**By cloud gap, 14 d:** sensitivity is 0.50 when the last clear optical image is at most 5 days
old, 0.33 at 6–15 days and 0.15 above 15 days. False alarms are highest above 15 days (19 per 100
fields, against 14–15). Long optical gaps remain the weak spot.

**By field size, 14 d:** precision is 0.27 on fields ≥ 5 ha against 0.22 on 2–5 ha. The sample
has no fields under 2 ha.

## Early warning (the replay story)

Onset is the first date a field enters a stress event. Events present from the first grid date
are excluded. Of the 29 onsets in 2024:
- **red:** 21 (72%) had an alarm in the 21 days before onset, median 15 days ahead (range 5–20);
- **amber or red:** 25 (86%) had an alarm beforehand, median 20 days ahead.

## Takeaways

- Warnings usually come 2–3 weeks before the canopy visibly falls behind its neighbours. That is
  what the US-11 replay shows.
- The cost is false alarms at 21 days. In practice, the 21-day light is a "watch" signal, and
  red at 7–14 days is the actionable one.
- Next: per-district calibration (chosen on validation) is the most promising fix for Coesfeld-type
  false alarms.
