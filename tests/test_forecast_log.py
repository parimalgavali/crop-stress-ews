from datetime import date

import pandas as pd

from cropews.forecast_log import append_log, outcomes_long, scoreboard


def _entries(day: str, risk: float, level: str, issued: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "field_id": ["a", "b"],
            "date": [day, day],
            "horizon_days": [7, 7],
            "risk": [risk, 0.1],
            "level": [level, "green"],
            "issued_at": [issued, issued],
        }
    )


def test_append_log_never_overwrites_an_issued_forecast(tmp_path) -> None:
    path = tmp_path / "log.csv"
    append_log(path, _entries("2027-04-05", 0.9, "red", "2027-04-05T06:00Z"))
    log = append_log(path, _entries("2027-04-05", 0.2, "green", "2027-04-06T06:00Z"))
    assert len(log) == 2
    assert log.set_index("field_id").loc["a", "risk"] == 0.9


def test_scoreboard_scores_only_after_the_window(tmp_path) -> None:
    log = append_log(tmp_path / "l.csv", _entries("2027-04-05", 0.9, "red", "t"))
    targets = pd.DataFrame(
        {"field_id": ["a", "b"], "date": pd.to_datetime(["2027-04-05"] * 2), "onset_7d": [1, 0]}
    )
    outcomes = outcomes_long(targets, (7,))
    early = scoreboard(log, outcomes, date(2027, 4, 11))["horizons"]["7"]
    assert early["scored"] == 0 and early["pending"] == 2
    late = scoreboard(log, outcomes, date(2027, 4, 12))["horizons"]["7"]
    assert late["scored"] == 2 and late["auroc"] == 1.0
    assert (late["red_hits"], late["red_false"], late["missed"]) == (1, 0, 0)


def test_scoreboard_counts_due_forecasts_without_outcome(tmp_path) -> None:
    log = append_log(tmp_path / "l.csv", _entries("2027-04-05", 0.9, "red", "t"))
    targets = pd.DataFrame(
        {"field_id": ["a"], "date": pd.to_datetime(["2027-04-05"]), "onset_7d": [1]}
    )
    h = scoreboard(log, outcomes_long(targets, (7,)), date(2027, 4, 12))["horizons"]["7"]
    assert (h["issued"], h["pending"], h["scored"], h["no_outcome"]) == (2, 0, 1, 1)


def test_scoreboard_marks_delayed_issuance_stale() -> None:
    # Review finding 4.3: a forecast logged with an origin before its issuance day must not
    # earn credit for events in the already-elapsed part of its window.
    log = append_log(tmp_path_fixture(), _entries("2027-04-05", 0.9, "red", "2027-04-10T06:00:00Z"))
    targets = pd.DataFrame(
        {"field_id": ["a", "b"], "date": pd.to_datetime(["2027-04-05"] * 2), "onset_7d": [1, 0]}
    )
    h = scoreboard(log, outcomes_long(targets, (7,)), date(2027, 4, 13))["horizons"]["7"]
    assert h["stale_origin"] == 2
    assert h["scored"] == 0
    # same-day issuance is aligned and scores normally
    log2 = append_log(
        tmp_path_fixture("l2"), _entries("2027-04-05", 0.9, "red", "2027-04-05T23:00:00Z")
    )
    h2 = scoreboard(log2, outcomes_long(targets, (7,)), date(2027, 4, 13))["horizons"]["7"]
    assert h2["stale_origin"] == 0 and h2["scored"] == 2


def tmp_path_fixture(name: str = "l"):
    import tempfile
    from pathlib import Path

    return Path(tempfile.mkdtemp()) / f"{name}.csv"


def test_scoreboard_splits_pending_outcome_from_unobservable(tmp_path) -> None:
    log = append_log(tmp_path / "l.csv", _entries("2027-04-05", 0.9, "red", "2027-04-05T06:00Z"))
    # "a" has a real outcome; "b" has a row but NaN label (permanently unobservable); "c"'s
    # forecast (added next) has no outcome row at all (still pending confirmation).
    targets = pd.DataFrame(
        {
            "field_id": ["a", "b"],
            "date": pd.to_datetime(["2027-04-05"] * 2),
            "onset_7d": [1, float("nan")],
        }
    )
    extra = _entries("2027-04-05", 0.4, "green", "2027-04-05T06:00Z")
    extra["field_id"] = ["c", "d"]
    extra["risk"] = [0.4, 0.2]
    log = append_log(tmp_path / "l.csv", extra)
    h = scoreboard(log, outcomes_long(targets, (7,), keep_nan=True), date(2027, 4, 13))["horizons"][
        "7"
    ]
    assert h["issued"] == 4
    assert h["evaluated"] == 1 and h["scored"] == 1
    assert h["unobservable"] == 1 and h["pending_outcome"] == 2
    assert h["no_outcome"] == h["pending_outcome"] + h["unobservable"]
    assert h["withheld"] == 0 and h["eligible"] == 4
