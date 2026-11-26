# ADR 0079: Explicit local-work backup

- Status: accepted, 2026-11-26; #176.
- One user-requested JSON download contains schema_version 1, export timestamp, saved field
  names/ids, checks (including notes), and structured observations. No upload or accounts.
- Photo references are kept but files, satellite images, caches and reports are explicitly
  excluded in the UI and file. Invalid JSON/unreadable storage fails visibly, never as an
  empty success. Existing visit-record JSON exports remain unchanged.
