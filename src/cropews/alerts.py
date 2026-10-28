"""Opt-in alerts when a Live field turns red (US-21, ADR 0022).

Each field has a public ntfy.sh topic. Anyone can subscribe to it in the ntfy app or browser,
so no names, e-mail addresses or chat ids are stored anywhere in this project.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

NTFY_URL = "https://ntfy.sh"
TOPIC_PREFIX = "cropews-nrw-"


def topic(field_id: str) -> str:
    return TOPIC_PREFIX + field_id.lower()


def _first_red(card: dict[str, Any]) -> dict[str, Any] | None:
    reds = [h for h in card.get("horizons", []) if h["level"] == "red"]
    return min(reds, key=lambda h: h["days"]) if reds else None


def new_red(prev: dict[str, Any] | None, cur: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Fields red now (earliest red horizon) that were not red in the previous run."""
    before = (prev or {}).get("risk", {})
    out = []
    for fid, card in sorted(cur.get("risk", {}).items()):
        h = _first_red(card)
        if h is not None and (fid not in before or _first_red(before[fid]) is None):
            out.append((fid, h))
    return out


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
