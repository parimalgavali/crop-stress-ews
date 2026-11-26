# Satellite clarity and upper read-aloud — #198–#205

Implemented in dependency order with individual story commits:

- #203: explicit patch-assessment sufficiency (>=10 clear finite pixels, >=80% interior coverage).
- #204: symbol-and-colour vegetation legend, within-field explanation and honest result limits.
- #198: dated graph, full NDVI scale and accessible observed-value table.
- #199: actual crop-group/district context with unique contributor counts.
- #200: supported same-date comparisons and visible changing coverage; public-data inspection
  recorded in ADR 0083 without diagnosing the screenshot's specific jump.
- #201: acquisition date, source/effective pixel spacing and explanation shared with speech.
- #202: overview and pixel view over the same on-demand raster, with stale-response protection.
- #205: one selected-field speaker at the top, icon/Stop, cancellation and unavailable feedback.
  Separately drawn fields keep their own labelled control.

Integrated the earlier merged predecessor-branch stack (#176–#179 plus vertical help legend),
which was not present on main after #193 was merged. No new data files or dependencies.

## Verification

- 79 web unit tests pass, including date-mismatch comparison, unknown/sparse support, patch
  sufficiency, photo-resolution messaging, stale photo responses, and speech cancellation.
- All 21 Playwright tests pass, including existing workflows and EN/DE satellite/speaker cases.
  Nine relevant accessibility/phone/print/satellite cases pass again after final hint refinements.
- ESLint (no warnings), TypeScript/build, ruff lint/format and mypy pass.
- Python: 178 passed, 5 PostGIS tests skipped because the service is unavailable locally.
- Local Python 3.14 uses project extras, not the Python 3.10 lock environment; CI uses 3.11.

## Rollout limits

Deployment is still triggered by merging to main. New patch-assessment and comparison-support
metadata appears on the next live extraction; push deployments reuse the previous Live data.
Until then, the UI conservatively labels old assessment/support as insufficient/unknown. No
model retraining, forecast changes, field validation, notifications or new live extraction run.
