# ADR 0084: Compact field visit

Status: accepted, 2026-11-27. Story #180.

Add an optional visit mode to the existing monitored-field Live card. Keep the current warning
card and field navigation. Show the personal name when saved, stable id, district, Live data
update date, shared evidence summary and three general inspection prompts. An absent forecast
is explicitly unavailable, never green. The existing warning guidance continues to distinguish
low risk from confirmed health. Charts and extra conditions remain in expandable details;
returning to full Live keeps the same field.

Reuse the existing device-local ObservationLog and schema. Keep a single mounted log across
mode changes so an unsaved form survives. Visit mode expands it and exposes its record button.
Saving must complete the storage write before showing success. If it fails, show an error and
retain the form. Require a visit date with the native form validator. Unknown severity/cause
and unreviewed status remain available; no inspection result is inferred from a warning.

The upper speaker receives the same checklist, date and limitations through the existing
LiveCard summary callback. No change to forecasts, thresholds, evidence assessments, storage
keys, backup schema, server APIs or sharing. This remains general inspection guidance.

CI regression: the upper speaker adds its own status region. Field-check E2E assertions must
select the matching status text rather than assume the page contains exactly one status.
