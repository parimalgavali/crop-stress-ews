# Device restore — #177

Added bilingual file preview, validation, default merge, explicitly confirmed replacement,
result counts and refreshed UI. One snapshot write makes restoration atomic if storage is full.

Validation: 71 web unit tests, eslint and TypeScript/build pass. Backup download → confirmed
replacement → refreshed saved fields → reload persistence passes in Playwright, as do all four
EN/DE axe checks. Merge deduplicates independent of object-key order and keeps checks in date
order; targeted restore tests and typecheck rerun after that adjustment. Ruff checks pass.
