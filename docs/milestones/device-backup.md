# Device backup — #176

Added explicit bilingual backup download with a dated filename and schema version. It includes
names, checks, notes and visit records and describes excluded files. No upload or new dependency.

Validation: 67 web unit tests, eslint and TypeScript/build pass. The Playwright saved-field
flow downloads a real backup and verifies its schema and stored field name. Ruff checks pass;
Python code is unchanged from the validated #175 base.
