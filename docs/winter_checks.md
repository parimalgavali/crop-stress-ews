# Winter checks (US-16, ADR 0016)

Six core districts, the same 40 sampled winter-wheat fields per district-season as the spring model,
1 October of the year before harvest to 31 March. Outcome: the field had a spring stress event
(ADR 0010 label). IACS has no emergence or flooding records, so this is the only field-level check
available in open data.

## Emergence vs same-date peers (Sentinel-2)

Flag: median winter NDVI peer z < −1.5 on ≥ 2 clear dates (Nov–Mar). Scale fitted on training
seasons only, pooled per district over the winter. AUROC uses the continuous score (−z).

| Split | Fields | Flagged | Spring event rate, flagged | Spring event rate, others | AUROC (95% CI) |
|---|---|---|---|---|---|
| train (2019–21, 2023) | 955 | 81 | 0.47 | 0.12 | 0.69 (0.63–0.74) |
| validation 2022 | 240 | 14 | 0.43 | 0.13 | 0.70 (0.61–0.78) |
| test 2024 | 224 | 1 | 0.00 | 0.13 | 0.56 (0.44–0.69) |
| extra check 2025 | 240 | 16 | 0.69 | 0.19 | 0.75 (0.66–0.83) |

- In most seasons a field that is clearly behind its neighbours in winter is 3–4× more likely to
  have a spring stress event. Much of this is a persistent field effect (weak fields stay weak); it is
  still useful because it is visible before 5 April.
- **It fails in the wet test season 2024.** Winter 2023/24 had few clear images (median 3 per
  field vs 4–9 in other winters) and no field fell far behind its peers (lowest z −1.8). The 2024
  spring problems came from the wet spring itself, which a winter greenness check cannot see.
- The pooled scale was chosen after seeing that per-10-day-bin scales left 2024 fields without a
  fitted scale (coverage, not the test metric, drove the change).

## Waterlogging (Sentinel-1 + rain)

Wet radar date: VV ≥ 3 dB below the field's winter median (same orbit direction) after ≥ 20 mm of
rain in the previous 7 days (DWD HYRAS). Thresholds are descriptive, not tuned.

WATERLOG_TABLE

## Limits

- No ground truth for emergence, sowing date or standing water.
- 40 fields per district-season; per-district numbers are noisy.
- The Live mode cannot use these checks until current winter-cereal parcels are known (US-18).

Reproduce: `python scripts/extract_s2.py --window winter ...`, `python scripts/extract_s1.py
--window winter ...`, then `python scripts/winter_check.py` and `python scripts/waterlog_check.py
--year 2024` (and `--year 2022`).
