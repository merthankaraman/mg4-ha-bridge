"""Localize command feedback attributes from translations/*.json."""

from __future__ import annotations

import json
from pathlib import Path

_TRANSLATIONS_DIR = Path(__file__).parent / "translations"
_CACHE: dict[str, dict] = {}


def _lang(hass) -> str:
    raw = getattr(getattr(hass, "config", None), "language", None) or "en"
    return str(raw).split("-")[0].lower()


def _load_section(lang: str) -> dict:
    """Return command_feedback section for lang (fallback: en, then {})."""
    if lang in _CACHE:
        return _CACHE[lang]

    section: dict = {}
    for candidate in (lang, "en"):
        path = _TRANSLATIONS_DIR / f"{candidate}.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            raw = data.get("command_feedback")
            if isinstance(raw, dict):
                section = raw
                break

    _CACHE[lang] = section
    return section


def _lookup(lang: str, group: str, key: str) -> str | None:
    section = _load_section(lang)
    bucket = section.get(group)
    if isinstance(bucket, dict) and key in bucket:
        value = bucket[key]
        return value if isinstance(value, str) else None
    if lang != "en":
        return _lookup("en", group, key)
    return None


def localize_detail(hass, key: str | None, arg: str | None = None) -> str | None:
    if not key:
        return None
    lang = _lang(hass)
    tmpl = _lookup(lang, "detail", key) or key
    if arg:
        arg = _localize_arg(lang, arg)
    if "{arg}" in tmpl:
        return tmpl.replace("{arg}", arg or "")
    if arg:
        return f"{tmpl} ({arg})"
    return tmpl


def _localize_arg(lang: str, arg: str) -> str:
    """Translate simple tokens inside args (on/off/start/stop/auto)."""
    parts = []
    for piece in arg.split("/"):
        piece = piece.strip()
        parts.append(_lookup(lang, "detail", piece) or piece)
    return "/".join(parts)


def localize_command(hass, command: str | None) -> str | None:
    if not command:
        return None
    lang = _lang(hass)
    return _lookup(lang, "command", command) or command
