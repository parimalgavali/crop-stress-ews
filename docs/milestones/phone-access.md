# Phone accessibility — #179

Improved control spacing, small-screen text reflow, help scrolling and amber symbol contrast.
Previous/next date buttons provide a non-drag alternative to the timeline. Physical phone and
outdoor/user trials remain future work; browser-emulated viewport checks are documented below.

Validation: 19/19 Playwright tests pass on macOS Chromium, including EN/DE replay + Live at
320×640 CSS pixels with doubled base text (36px), no document horizontal overflow, usable help,
48px controls and button-based date changes. Existing keyboard, printing, offline and axe
checks pass. 72 web unit tests, eslint and TypeScript/build pass; ruff/mypy pass and pytest
175 passed, five PostGIS-dependent tests skipped locally. No physical-device or outdoor trial.

Owner follow-up, 27 Nov: stacked the three help-legend entries vertically in English and
German, using a semantic list and keeping each icon beside its explanation.
