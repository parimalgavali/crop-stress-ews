# Readable visit CSV — #182

Implemented 2026-11-27. All stored visits can be exported with readable bilingual headings,
current personal field names, dates, findings, unknown severity/cause, review status and notes.
The existing JSON export remains available. CSV is labelled for spreadsheet reading and analysis;
the normal backup is the restore format. No local records are modified during export.

Validation includes UTF-8, quoted/multiline notes, review states, formula-injection strings in
ids/names/notes, Unicode leading controls, unreadable storage and an actual browser download.
Build/typecheck and lint pass; 100 web unit tests and 25 browser scenarios pass. Python checks
were already clean before these web-only stories (178 passed, 5 local PostGIS skips).
