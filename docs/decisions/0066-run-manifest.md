# ADR 0066: Run manifest + expected-output check (spec 8.5)

- Status: accepted, 2026-10-26
- Context: Spec 8.5 — the reproducible bundle needs input size, parameter values,
  runtime and an expected-output check. The demo run already proved the causal chain;
  the manifest needed to become verifiable.
- Decision: the manifest now carries observations count, parameters (horizons, dip
  magnitudes, split rule, min_peers, doy_bin), runtime_seconds, python version and an
  artifact_sha256 over the stable keys. `fixtures/demo_expected.json` is the checked-in
  expected output; `--check fixtures/demo_expected.json` diffs ignoring volatile keys
  (runtime_seconds, python). Cost stays honest: runtime is recorded, not claimed.
