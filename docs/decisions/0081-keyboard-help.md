# ADR 0081: Keyboard path and help focus

- Status: accepted, 2026-11-26; #178.
- Existing macOS keyboard test failed before selecting a field, on unchanged main as well.
  It drove native select popups with arrows. Keep the native select; wait for options and test
  native type-ahead ('f' selects the first Field option) without OS popup automation.
- Add a skip-to-field-controls link. The help dialog focuses its sole close button, contains
  Tab/Shift+Tab, closes with Escape, and restores focus to its opener. Native details/forms
  keep their normal keyboard interactions. Existing visible focus styles are retained.
- Automated keyboard tests are not a claim of comprehensive screen-reader or user validation.
