# Agent Instructions

Before making project decisions or code changes, read:

1. `docs/project_memory.md`
2. `docs/decisions/README.md` and the relevant decision records

Chat history is not the source of project intent; these documents are.

## Memory maintenance

Before every commit, check whether the change introduced or changed a project assumption,
data/label policy, modeling or evaluation decision, milestone, dependency, or a data-inspection
result future sessions need. If yes, update `docs/project_memory.md` and add or amend a record in
`docs/decisions/`. After each milestone, add a summary under `docs/milestones/`.

## Data policy

`data/` and `outputs/` are git-ignored. Do not commit raw or derived data, models, or caches.
Only exception: the static demo files `web/public/demo/<year>.json` (ADR 0014).
Respect source licences (see `docs/decisions/0002-data-sources.md`); UFZ drought-monitor data is
non-commercial and must not be redistributed.

## Checks

`ruff check . && ruff format --check . && mypy && pytest -q` (also run in CI and pre-commit).
