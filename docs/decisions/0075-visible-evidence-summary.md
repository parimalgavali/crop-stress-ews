# ADR 0075: Show evidence quality before Live conditions

- Status: accepted, 2026-11-26
- Context: #170 asks users to see evidence limits without opening details.
- Decision: show the existing quality status and last clear satellite photo above the Live
  conditions, and use the same summary in read-aloud. Existing expanded evidence remains.
  Missing status is explicitly unknown (including in expanded evidence); it is not inferred
  from a green light or from the presence of an image. Use condition metadata as a fallback
  for photo freshness only. No new confidence score, thresholds or model computation.
