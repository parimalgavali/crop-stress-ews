# ADR 0086: Readable visit CSV

Status: accepted, 2026-11-27. Story #182.

Offer CSV alongside the original observation JSON export. The CSV reads current stored visits
and saved field names, validates those two sources through the existing backup schema, and
reports unreadable data without changing it. It exports all stored visits, including fields
not currently selected. No forecast, review decision or diagnosis is inferred.

Use readable EN/DE headers and category labels: field id, personal name (or explicit unnamed),
visit date, visitor, finding, severity, suspected cause, review status and note. Unknown severity
and cause remain "not sure"; unreviewed remains explicit. Shared observation text avoids two
sets of category translations. Field names are the current local names, not historical aliases.

Use standard comma-separated, fully quoted cells, doubled embedded quotes, CRLF rows and a
UTF-8 BOM for Excel. Preserve non-English characters and multiline notes. Prefix a literal
apostrophe to any cell whose first meaningful character is =, +, - or @ after whitespace or
Unicode control/format characters, and to cells beginning with tab/newline/CR. Apply this to
all cells, including field ids, names and notes. This neutralises formula interpretation while
leaving the stored text unchanged.

CSV is a reading/analysis report, not an import or restore format. Keep existing JSON export
and normal backup/restore, and explain private notes and unreviewed observations in the UI.
No new storage keys or schema changes. Photo files are not part of this tabular report.
