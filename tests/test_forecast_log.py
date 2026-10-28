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
