# ADR 0080: Previewed, atomic restoration of local work

- Status: accepted, 2026-11-26; #177.
- Validate schema, types, dates, enumerations, duplicate field ids and a 5 MB file limit before
  showing a preview of counts/date. Invalid or unsupported files do not change storage.
- Default merge keeps existing field names and deduplicates identical records. Replace needs an
  explicit acknowledgement and a final Restore click. Unmonitored ids remain visible in My fields.
- Local work after restore is stored as one cropews.local-data.v1 snapshot containing the three
  work-key JSON strings. Browser readers/writers use localDataStore; legacy data is read until a
  snapshot exists, then snapshot takes precedence. Restore commits in one localStorage write:
  quota failure cannot leave half-restored data. Legacy keys are retained but not used after restore.
- UI refreshes saved fields and visit records on success and shows resulting counts. Files/photos
  excluded from backup are not recreated. No upload or account. Existing small exports remain.
