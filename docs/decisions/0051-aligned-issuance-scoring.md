# ADR 0051: Only forecasts issued on their origin day earn outcome credit

- Status: accepted, 2026-10-26
- Context: Review finding 4.3 — a delayed/manual run picks the last grid step <= as_of as the
  forecast `date`, so part of its nominal window (origin, origin+horizon] has already elapsed at
  issuance and the log could be credited for events before the forecast existed.
- Decision: the prospective scoreboard flags rows whose `issued_at` day is after the origin `date`
  as `stale_origin` and never scores them (aligned-schedule policy: a forecast is only evaluated
  when issued on its origin day). Log rows now also carry `model_version` (from the model bundle,
  empty for older entries); `issued_at` continues to record the run timestamp.
- Limits: an early-morning run may still use a partially-observed weather day (intraday issuance
  lag is not modelled). Historic rows without `model_version` are left untouched — the first
  issuance is never overwritten (ADR 0020 stands).
