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

## #198: Readable greenness chart

Show dated endpoints and the full NDVI −1..1 scale, without clipping negative observations.
A native details/table exposes all measured dates/values. Explain that dots are observations,
lines only connect them, and greenness is not health percentage or yield. The description is
also in read-aloud. No values are interpolated into the data.

## #199: Describe the actual comparison group

Expose the district, mixed-crop versus likely-cereal group, date and contributing field count.
Unknown metadata is labelled unknown, never assumed to mean wheat. The same context appears
in the chart and speech; lower greenness does not prove poor health. season_series collapses
overlapping clear observations to a field/date median before computing district medians and
unique contributor counts. It reports previous count and retained membership for coverage
interpretation; no field identities or model changes are added.

## #200: Same-date supported comparison, changing coverage visible

The descriptive above/same/below statement requires an exact field/group observation-date
match, a known crop-group kind, and at least five known unique contributors (existing minimum).
No prior-date carry-forward or invented daily values. Raw peer medians remain plotted and a
table reports date, count and changing membership; missing metadata is unknown. This avoids
silently smoothing jumps or calling group turnover crop damage. Forecast models are untouched.

Public-data inspection, 2026-11-27: published as_of=2026-11-26, peer_kind=all. Reconstructing
contributors from published per-field clear dates found group membership changing in 17/17
adjacent eligible-date pairs in Coesfeld, 7/7 Düren, 12/12 Höxter, 13/13 Rhein-Erft-Kreis,
15/15 Soest and 12/13 Warendorf. This establishes changing coverage, not the cause of any
particular plotted jump; the screenshot's field was not identified. New membership metadata
requires a new live extraction. Legacy data stays visible but without unsupported comparisons.

## #201: Source resolution versus extracted detail

Photo metadata reports actual acquisition date and effective extraction spacing separately
from the 10 m Sentinel-2 colour source. Explain coarser large-field reads, cloudy-versus-detailed
views, transparent exterior/no-data and ambiguous brown colours, visibly and in speech. Reject
next-day STAC results and ignore late responses after the selected field/date changes. No
satellite photo is fetched until requested.

## #202: Honest pixel view

Overview and enlarged-pixel modes share the same unchanged canvas raster; nearest-neighbour
CSS rendering reveals blocks in pixel mode, not invented detail. Sizing is bounded by raster
width and phone width. Date, attribution and resolution metadata remain visible. Switching
modes does not fetch another image. Source masks and pixel values are preserved; no sharpening.
