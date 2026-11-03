# ADR 0056: Pinned dependency lock

- Status: accepted, 2026-10-26
- Context: Review 4.8 — rerun instructions need a reproducible environment, not only version
  ranges. pyproject ranges are kept for the package itself.
- Decision: `requirements-lock.txt` pins the full resolved tree for all extras
  (extract, model, seq, api, dev), generated with `pip-compile` on Python 3.10.
  Reproduce: `python -m venv .venv && pip install -r requirements-lock.txt -e .`
  Regenerate after dependency changes: `pip install pip-tools && pip-compile --extra extract
  --extra model --extra seq --extra api --extra dev -o requirements-lock.txt pyproject.toml`.
