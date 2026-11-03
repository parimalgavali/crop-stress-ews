def test_manifest_reports_inputs_runtime_and_stable_expected() -> None:
    import json
    from pathlib import Path

    from cropews.demo_evaluation import _stable, run

    m = run()
    for key in (
        "synthetic",
        "observations",
        "parameters",
        "runtime_seconds",
        "lead_time",
        "horizons",
    ):
        assert key in m
    m["python"] = "x"
    expected = json.loads(Path("fixtures/demo_expected.json").read_text())
    m["entry_point"] = expected["entry_point"]
    m["artifact_sha256"] = expected["artifact_sha256"]
    assert _stable(expected) == _stable(m)
