# Field visit view — #180

Implemented 2026-11-27. A farmer can open a monitored field, start a visit, read the existing
warning and evidence dates, use a short checklist and record an observation on the same screen.
Charts remain available in details and full Live is one button away. English and German copy
and read-aloud share the guidance. Storage errors retain unsaved input and report failure.

Validation: production build, ESLint, 82 web unit tests and 21 Playwright tests pass. Browser
coverage includes saving standing water, shared speech, existing full Live, phone reflow and
EN/DE axe checks with the visit form open. Python ruff, format and mypy pass; 178 tests pass,
5 PostGIS-dependent tests skipped locally. The earlier CI status-locator regression is fixed.
No deployment or merge is performed by this milestone.
