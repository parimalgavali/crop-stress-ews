# ADR 0083: Satellite views communicate evidence and limits

Status: accepted, 2026-11-27.

## #203: Patch assessment

A no-patches statement requires at least 10 finite clear interior pixels (existing analysis
minimum) and at least 80% of the full interior clear and finite (the existing clear-observation
rule). Missing pixels count against coverage. Assessment reports detected / none_detected /
insufficient with coverage and pixel count. These are reporting guards, not validated agronomic
thresholds. Cloud/shadow cells are excluded from the display. Legacy payloads without an
assessment are conservatively unknown/insufficient until a new live extraction runs. The UI and
read-aloud share patchSummary. No state confirms crop health or changes served forecasts.

## #204: Interpreting the patch map

Use symbols plus colour for greenness, candidate areas and unavailable/exterior cells. The
legend explains the within-field comparison separately from district comparisons; describes
20 m analysis, minimum four connected pixels and potentially aggregated display cells. Visible
and spoken descriptions share the result and limits. The grid shrinks to phone width. Missing
assessment also gets an explicit message when no subfield entry exists.
