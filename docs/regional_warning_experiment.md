# Could a separate warning spot problems across a whole district?

**Status: research plan only; not implemented or validated.** Story #172.

## Why test it?

The current model asks whether one field will fall behind nearby wheat fields. If a dry spell
or other problem affects all those fields similarly, none may fall behind its neighbours.
A regional warning would ask a different question: "Is this district experiencing unusual
conditions that deserve a closer look?" It must be separate from field-level risk.

Example: every wheat field could be less green than usual while still looking similar to its
neighbours. A future regional signal could add context, but it would not identify a cause,
prove harvest loss, or tell a farmer which treatment to use.

## Agree the outcome before building the model

Find a partner able to supply dated, district-level crop observations with a consistent rubric
and adequate coverage. Define the event, forecast window, reporting delay and uncertain cases
before inspecting candidate model scores. Reviewers should not see model warnings while
assigning outcomes. Record permissions and licences; do not assume gated data is available.

Do not reuse the field-versus-peer canopy label as proof that district-wide warnings work.
Annual district yields may be a secondary end-of-season check, but cannot establish the date
or cause of a spring event. The previous district harvest outlook failed its baseline
([case study](case_study.md)); do not repackage it as a successful regional warning.
Without independent dated outcomes, stop at descriptive weather context, not risk probabilities.

## Run a bounded comparison

1. Freeze one outcome and forecast window with the partner. Fix the practical visit budget,
   acceptable false-warning burden and minimum useful improvement before fitting anything.
2. Test simple baselines first: recent district condition persisting, training-season seasonal
   norm, and an agreed weather-only rule. Historical vegetation departures and weather totals
   are candidates, not assumed useful predictors.
3. Use only inputs actually available at each issue date, including publication delays.
   Fit normal ranges, missing-data rules, thresholds and calibration on training seasons only.
   Do not tune with the 2024 or 2025 outcomes already examined during development.
4. Use season-held-out development checks, then freeze the choice before a genuinely future
   season. Districts in one season share weather: resample whole seasons/district-season blocks
   as appropriate, rather than treating daily rows or nearby fields as independent samples.
5. Report useful warnings, missed events, false-warning episodes, lead time, missing outcomes
   and calibration. Compare paired results on identical eligible dates with uncertainty.
   Field-bootstrap intervals from ADR 0054 cannot be copied unchanged to a regional experiment.
6. Check each district and missing-data condition. If there are too few independent seasons or
   events for a stable comparison, call the result inconclusive and collect more evidence.

## Adoption or rejection

Adopt only if the frozen candidate beats the best simple baseline by the pre-agreed practical
margin, uncertainty supports a positive difference, alert burden stays within the agreed
limit, and a future-season check plus adviser review supports usefulness. Otherwise reject
or keep it as research; document the failure and avoid changing current field predictions.

If adopted later, show a separately labelled regional context message with its date, coverage
and uncertainty. Never turn every field red solely because the regional indicator is high.
The current served model, labels and thresholds remain unchanged by this plan.
