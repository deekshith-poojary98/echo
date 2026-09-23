from __future__ import annotations

from datetime import datetime, timezone

from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation

_UTC = timezone.utc


def _require_secs(value: object, method: str, location: SourceLocation | None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EchoTypeError(f"{method}() seconds must be an int", location, code="E2851")
    return value


def _require_count(value: object, method: str, location: SourceLocation | None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EchoTypeError(f"{method}() requires an int", location, code="E2851")
    return value


def _require_text(value: object, method: str, location: SourceLocation | None) -> str:
    if not isinstance(value, str):
        raise EchoTypeError(f"{method}() text must be a string", location, code="E2851")
    return value


def _require_pattern(value: object, method: str, location: SourceLocation | None) -> str:
    if not isinstance(value, str):
        raise EchoTypeError(f"{method}() pattern must be a string", location, code="E2851")
    return value


def format_time(secs: object, pattern: object, location: SourceLocation | None = None) -> str:
    stamp = _require_secs(secs, "formatTime", location)
    fmt = _require_pattern(pattern, "formatTime", location)
    try:
        return datetime.fromtimestamp(stamp, tz=_UTC).strftime(fmt)
    except (OverflowError, OSError, ValueError) as exc:
        raise EchoRuntimeError(f"cannot format time: {exc}", location, code="E2851") from exc


def parse_time(text: object, pattern: object, location: SourceLocation | None = None) -> int:
    value = _require_text(text, "parseTime", location)
    fmt = _require_pattern(pattern, "parseTime", location)
    try:
        parsed = datetime.strptime(value, fmt)
    except ValueError as exc:
        raise EchoRuntimeError(f"cannot parse time: {exc}", location, code="E2851") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_UTC)
    else:
        parsed = parsed.astimezone(_UTC)
    try:
        return int(parsed.timestamp())
    except (OverflowError, OSError, ValueError) as exc:
        raise EchoRuntimeError(f"cannot parse time: {exc}", location, code="E2851") from exc


def days(count: object, location: SourceLocation | None = None) -> int:
    return _require_count(count, "days", location) * 86_400


def hours(count: object, location: SourceLocation | None = None) -> int:
    return _require_count(count, "hours", location) * 3_600


def minutes(count: object, location: SourceLocation | None = None) -> int:
    return _require_count(count, "minutes", location) * 60
