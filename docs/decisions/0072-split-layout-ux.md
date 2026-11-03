# ADR 0072: Split map/info layout and low-literacy UX pass

- Status: accepted, 2026-11-04
- Context: the field card grew long (status lines, weather, chart, patch map,
  photo, evidence, checks, notes, utilities). Users had to scroll to see
  everything, and the Listen button sat at the bottom where low-literacy users —
  its target audience — would never find it.
- Decision:
  - Desktop: `.main` is a 50/50 split — map on the left, field panel on the
    right — each scrolling independently; the field picker and prev/next buttons
    sit in a sticky `.panel-tools` block that stays visible while scrolling.
  - Mobile: the map keeps 45 vh when nothing is selected and shrinks to 26 vh
    once a field is chosen (`main.has-selection`), so the card is visible
    immediately without scrolling past a full map.
  - Card order for low-literacy users: status lines → Listen button (primary
    action, moved from the bottom to directly under the status) → "I checked it"
    → weather strip → season chart → patch map → photo → evidence details →
    spring note → collapsed "More things you can do" section holding the
    secondary utilities (alerts, field link, print, visit log).
- Consequences: only visible-information order changed; no data or evaluation
  logic was touched. Utilities are one tap away behind an expandable section
  rather than removed, keeping the card scannable.
- Follow-up fix (same day, found in UI verification): `.app` was
  `grid-template-rows: auto 1fr auto`, so the `.overview` strip stole the `1fr`
  row and squeezed `.main` — on phones the Live card was invisible without
  scrolling, and desktop showed an empty band. `.app` is now a flex column and
  `.main` takes `flex: 1` regardless of how many bars render above/below it.
