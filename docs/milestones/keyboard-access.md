# Keyboard access — #178

Added skip link and accessible help-dialog focus handling. Investigated the existing macOS
field-selection failure and kept native selection while testing keyboard type-ahead.

Validation: all 17 Playwright tests pass on macOS Chromium, including the formerly failing
keyboard selection, help focus containment/return, keyboard read-aloud/details/visit saving,
and four EN/DE axe checks. 72 web unit tests, eslint and TypeScript/build pass; ruff checks pass.
Human screen-reader and usability sessions remain #188, not claimed here.
