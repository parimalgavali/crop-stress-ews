# Scope

**Problem:** warn 7, 14 and 21 days ahead when a winter-wheat field in NRW is likely to enter a
stress event, using only data available on the prediction date.

**Metrics:** AUROC, AUPRC, sensitivity at fixed specificity, Brier score / calibration, false
alarms per field and season, lead time. Every model must beat a persistence baseline.

**Deliverables:** reproducible pipeline, evaluation report, model card, FastAPI + PostGIS service,
one-screen React map UI with a 2024 season replay, demo video.

**Non-goals:** real farmer users, paid APIs, field sensors, chat interfaces, logins.
