# ADR 0082: Phone controls and enlarged-text reflow

- Status: accepted, 2026-11-26; #179.
- App controls use 48 px minimum button height/width; checkbox/radio labels provide additional
  tap space. Preserve native control semantics and visible focus. Amber symbols use dark text.
- On small screens use document scrolling, wrapping controls and flexible widths so large text
  and the header cannot consume the entire scrollable field panel. Help scrolls within viewport.
- Add previous/next date buttons alongside the range timeline. Field selection already has a
  list alternative to map interaction; drawing uses individual taps, not a drag requirement.
- Validate EN/DE at a 320×640 CSS viewport and doubled base font, plus existing axe/keyboard
  flows. This is automated reflow testing, not a claim of physical-device/outdoor or universal
  screen-reader validation; participant testing remains #188.
