# Error analysis — test season 2024 (US-12)

`python scripts/error_analysis.py [--level red|amber]` joins the exported traffic lights
(`data/outputs/predictions.parquet`, [ADR 0012](decisions/0012-api-and-demo-model.md)) to the
labels, the field size and the Sentinel-2 cloud gap (`s2_days_since`, the number of days since the
last clear optical image). Code: `cropews.errors`.

**Scope: preliminary, Soest only (40 field-seasons).** Rerun this once the six-district Sentinel-1
extraction is complete. With 3–34 events per cell, treat every number below as indicative.

## Red alarms (90% validation specificity)

| Horizon | Events | Sensitivity | False alarms / 100 fields | Precision |
|---|---|---|---|---|
| 7 d | 12 | 0.17 | 25 | 0.17 |
| 14 d | 26 | 0.31 | 62 | 0.24 |
| 21 d | 34 | 0.47 | 133 | 0.23 |

The counts are per field-season over the whole season. One field can raise several alarms.

**By cloud gap, 14 d:** sensitivity is 0.50 when the last clear image is at most 5 days old,
0.14 at 6–15 days and 0.27 above 15 days. False alarms are highest above 15 days (30 per 100
fields, against 16–18). Long optical gaps are where the model is least reliable, so radar
coverage matters ([sequence-model ablation](sequence_models.md)).

**By field size:** large fields (≥ 5 ha) carry most events and get better precision (14 d: 0.40
against 0.11). The 30-field sample has no fields under 2 ha.

## Early warning (the replay story)

Onset is the first date a field enters a stress event. Events present from the first grid date
are excluded. Of the 9 onsets in 2024:
- **red:** 6 (67%) had an alarm in the 21 days before onset, median 17.5 days ahead (range 5–20);
- **amber or red:** 8 (89%) had an alarm beforehand, median 17.5 days ahead.

## Takeaways

- Warnings usually come 2–3 weeks before the canopy visibly falls behind its neighbours. That is
  what the US-11 replay shows.
- The cost is false alarms at 21 days. In practice, the 21-day light is a "watch" signal, and
  red at 7–14 days is the actionable one.
- Next: rerun on all six districts and report results by district.
