# Offline visit packs — #181

Implemented 2026-11-27 after the field visit view (#180). Farmers choose monitored fields,
prepare the app for offline use and save dated, bilingual snapshots of boundaries, warning
availability, evidence and checklists. Saved visits open without Live data. They support the
original local visit records, a static boundary outline and read-aloud. Removing a pack retains
records. Packs are excluded from ordinary backups; storage and online-feature limits are shown.

Preparation is acknowledged only after the app downloads succeed and JS/CSS content types are
checked. This rejects static-host HTML fallbacks for missing assets. Failed downloads, full or
unreadable storage preserve prior packs and cannot produce a saved-success message.

Validation: build/typecheck and ESLint pass; 88 web unit tests pass. All 25 browser scenarios
pass across the full regression run and targeted new scenarios: 16 existing app flows, six
EN/DE axe checks (including phone saved-visit forms) and three production service-worker tests.
The latter cover reopening and recording with networking disabled, removing only the pack,
and rejecting an unavailable required stylesheet. No model, Python dependency or backend change.
PR deployment/merge remains separate.
