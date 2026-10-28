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


def test_send_posts_to_field_topic() -> None:
    calls = []

    class Ok:
        ok = True

    def post(url, **kw):  # type: ignore[no-untyped-def]
        calls.append(url)
        return Ok()

    assert send(new_red(None, {"risk": {"LWK-9": _card("red")}}), "2027-04-10", post) == 1
    assert calls == ["https://ntfy.sh/" + topic("LWK-9")] and topic("LWK-9") == "cropews-nrw-lwk-9"
