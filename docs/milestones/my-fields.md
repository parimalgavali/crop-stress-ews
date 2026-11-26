# Saved fields — #175

Live users can save, rename, reopen and remove their monitored fields on the device. The saved
list shows available risk, missing forecasts and fields no longer monitored. Storage failure is
visible. English/German supported; model inputs and forecasts are unchanged.

Validation: 63 web unit tests, lint, TypeScript/build, saved-fields persistence browser flow
and all four EN/DE axe checks pass. Python: ruff lint/format, mypy and pytest pass (175 passed,
5 PostGIS-dependent tests skipped locally). Existing macOS keyboard test is handled in #178.
