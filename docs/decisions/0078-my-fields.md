# ADR 0078: Personal names for saved Live fields

- Status: accepted, 2026-11-26; story #175.
- My fields stores field_id, name (up to 80 characters) and district in the device browser,
  under cropews.saved-fields.v1. No account or upload. Only stable Live ids are saved;
  replay ids are not stable (ADR 0034). Removed monitored fields remain listed as unavailable.
- Saved names are display metadata, never a change to field identity, eligibility or risk.
  The list uses available Live forecasts and explicitly distinguishes no forecast from low risk.
- Failed writes show an error and do not claim success. Removing a favourite keeps visit records.
  Backup/restore follows in #176/#177; this story does not copy photos or observations.
