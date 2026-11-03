"""Opt-in alerts when a Live field turns red (US-21, ADR 0022).

Each field has a public ntfy.sh topic. Anyone can subscribe to it in the ntfy app or browser,
so no names, e-mail addresses or chat ids are stored anywhere in this project.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

import requests

NTFY_URL = "https://ntfy.sh"
TOPIC_PREFIX = "cropews-nrw-"


def topic(field_id: str) -> str:
    return TOPIC_PREFIX + field_id.lower()


def _first_red(card: dict[str, Any]) -> dict[str, Any] | None:
    reds = [h for h in card.get("horizons", []) if h["level"] == "red"]
    return min(reds, key=lambda h: h["days"]) if reds else None


# A field that flaps red -> not-red -> red inside this window is the same alert episode and
# must not re-alert (spec: false-alert episode handling). After the cooldown a fresh red is a
# new episode and alerts again.
COOLDOWN_DAYS = 10


def _last_alert(state: dict[str, Any], fid: str) -> date | None:
    raw = (state.get(fid) or {}).get("last_alert_at")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def new_red(prev: dict[str, Any] | None, cur: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Fields red now (earliest red horizon) that were not red in the previous run and are not
    inside the cooldown of a previous alert episode."""
    before = (prev or {}).get("risk", {})
    state = cur.get("alert_state") or (prev or {}).get("alert_state") or {}
    as_of = date.fromisoformat(str(cur.get("as_of") or "1970-01-01"))
    out = []
    for fid, card in sorted(cur.get("risk", {}).items()):
        h = _first_red(card)
        if h is None or (fid in before and _first_red(before[fid]) is not None):
            continue
        last = _last_alert(state, fid)
        if last is not None and (as_of - last).days < COOLDOWN_DAYS:
            continue
        out.append((fid, h))
    return out


def update_alert_state(
    cur: dict[str, Any], alerted: list[tuple[str, dict[str, Any]]]
) -> dict[str, Any]:
    """Stamp ``alert_state`` onto the payload: each alerted field records this run's as_of as
    its episode's last alert; state for fields not alerted carries over unchanged."""
    state = dict(cur.get("alert_state") or {})
    for fid, _h in alerted:
        state[fid] = {"last_alert_at": cur["as_of"]}
    cur["alert_state"] = state
    return cur


def message(field_id: str, h: dict[str, Any], as_of: str) -> tuple[str, str]:
    """Title and body in English, then German, with the same reasons as the UI."""
    en = ", ".join(r["text_en"] for r in h["reasons"]) or "no single main reason"
    de = ", ".join(r["text_de"] for r in h["reasons"]) or "kein einzelner Hauptgrund"
    d = h["days"]
    title = f"Field {field_id}: high risk / hohes Risiko ({d} d)"
    body = (
        f"High risk of crop stress in the next {d} days (as of {as_of}). Why: {en}.\n"
        f"Hohes Risiko für Pflanzenstress in den nächsten {d} Tagen (Stand {as_of}). "
        f"Warum: {de}.\n"
        "Satellite-based estimate, not yet checked in the field. / "
        "Schätzung aus Satellitendaten, noch nicht im Feld geprüft."
    )
    return title, body


def send(
    alerts: list[tuple[str, dict[str, Any]]],
    as_of: str,
    post: Callable[..., Any] = requests.post,
) -> int:
    """POST each alert to its field topic; returns how many were accepted."""
    sent = 0
    for fid, h in alerts:
        title, body = message(fid, h, as_of)
        res = post(
            f"{NTFY_URL}/{topic(fid)}",
            data=body.encode(),
            headers={"Title": title.encode(), "Tags": "warning", "Priority": "high"},
            timeout=20,
        )
        sent += int(getattr(res, "ok", False))
    return sent
