import pytest

from cropews.alerts import message, new_red, send, topic

REASON = {"code": "weak_canopy", "text_en": "Crop is behind", "text_de": "Bestand liegt zurück"}


def _card(*levels: str) -> dict:
    return {
        "horizons": [
            {"days": d, "risk": 0.5, "level": lv, "reasons": [REASON]}
            for d, lv in zip((7, 14, 21), levels, strict=False)
        ]
    }


def test_new_red_only_when_not_red_before() -> None:
    prev = {"risk": {"a": _card("red", "red", "red"), "b": _card("green", "amber", "green")}}
    cur = {
        "risk": {
            "a": _card("red", "red", "red"),
            "b": _card("green", "red", "red"),
            "c": _card("green", "green", "red"),
            "d": _card("green", "green", "green"),
        }
    }
    out = new_red(prev, cur)
    assert [(f, h["days"]) for f, h in out] == [("b", 14), ("c", 21)]
    assert [f for f, _ in new_red(None, cur)] == ["a", "b", "c"]


def test_message_is_bilingual_with_ui_reasons() -> None:
    title, body = message("LWK-1", _card("red")["horizons"][0], "2027-04-10")
    assert "LWK-1" in title and "7 d" in title
    assert "Crop is behind" in body and "Bestand liegt zurück" in body
    assert "falling behind nearby wheat fields in the next 7 days" in body
    assert "hinter benachbarte Weizenfelder" in body
    assert "Inspect the field" in body and "Bitte das Feld ansehen" in body
    assert "cause is unknown" in body and "Ursache ist unbekannt" in body
    assert "not a treatment recommendation" in body


def _recorder() -> tuple[list, object]:
    calls: list = []

    class Ok:
        ok = True

    def post(url, **kw):  # type: ignore[no-untyped-def]
        calls.append((url, kw["headers"]))
        return Ok()

    return calls, post


def test_send_posts_to_field_topic_with_token() -> None:
    calls, post = _recorder()
    alerts = new_red(None, {"risk": {"LWK-9": _card("red")}})
    assert send(alerts, "2027-04-10", post, token="tk", url="https://ntfy.example/") == 1
    [(url, headers)] = calls
    assert url == "https://ntfy.example/" + topic("LWK-9") and topic("LWK-9") == "cropews-nrw-lwk-9"
    assert headers["Authorization"] == "Bearer tk"


def test_send_without_token_sends_nothing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("NTFY_TOKEN", raising=False)
    calls, post = _recorder()
    assert send(new_red(None, {"risk": {"LWK-9": _card("red")}}), "2027-04-10", post) == 0
    assert calls == []


def test_send_reads_token_and_server_from_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("NTFY_TOKEN", "envtk")
    monkeypatch.setenv("NTFY_URL", "https://ntfy.example")
    calls, post = _recorder()
    assert send(new_red(None, {"risk": {"a": _card("red")}}), "2027-04-10", post) == 1
    assert calls[0][0] == "https://ntfy.example/cropews-nrw-a"
    assert calls[0][1]["Authorization"] == "Bearer envtk"


def test_cooldown_suppresses_flap_within_episode() -> None:
    from cropews.alerts import new_red, update_alert_state

    day0 = {"as_of": "2027-04-10", "risk": {"a": _card("red")}}
    assert [f for f, _ in new_red(None, day0)] == ["a"]
    update_alert_state(day0, new_red(None, day0))

    day1 = {"as_of": "2027-04-15", "risk": {"a": _card("green")}}
    day1["alert_state"] = day0["alert_state"]
    assert new_red(day0, day1) == []

    # Flap back to red 5 days after the alert -> same episode, suppressed.
    day2 = {"as_of": "2027-04-15", "risk": {"a": _card("red")}, "alert_state": day0["alert_state"]}
    assert new_red(day1, day2) == []

    # A fresh red after the cooldown is a new episode and alerts again.
    day3 = {
        "as_of": "2027-04-25",
        "risk": {"a": _card("red")},
        "alert_state": day0["alert_state"],
    }
    assert [f for f, _ in new_red({"risk": {"a": _card("green")}}, day3)] == ["a"]

    # A field that stayed red never re-alerts.
    day4 = {
        "as_of": "2027-05-10",
        "risk": {"a": _card("red")},
        "alert_state": day0["alert_state"],
    }
    assert new_red({"risk": {"a": _card("red")}}, day4) == []


def test_send_refuses_plain_http() -> None:
    calls, post = _recorder()
    alerts = new_red(None, {"risk": {"a": _card("red")}})
    with pytest.raises(ValueError):
        send(alerts, "2027-04-10", post, token="tk", url="http://ntfy.example")
    assert calls == []
