from __future__ import annotations

import re

from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation


def _compile(pattern: object, method: str, location: SourceLocation | None) -> re.Pattern[str]:
    if not isinstance(pattern, str):
        raise EchoTypeError(f"{method}() pattern must be a string", location, code="E2850")
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise EchoRuntimeError(f"invalid regex: {exc}", location, code="E2850") from exc


def _require_text(value: object, method: str, location: SourceLocation | None) -> str:
    if not isinstance(value, str):
        raise EchoTypeError(f"{method}() text must be a string", location, code="E2850")
    return value


def regex_match(text: object, pattern: object, location: SourceLocation | None = None) -> bool:
    value = _require_text(text, "regexMatch", location)
    compiled = _compile(pattern, "regexMatch", location)
    return compiled.search(value) is not None


def regex_find(text: object, pattern: object, location: SourceLocation | None = None) -> str | None:
    value = _require_text(text, "regexFind", location)
    compiled = _compile(pattern, "regexFind", location)
    match = compiled.search(value)
    if match is None:
        return None
    return match.group(0)


def regex_replace(
    text: object,
    pattern: object,
    replacement: object,
    location: SourceLocation | None = None,
) -> str:
    value = _require_text(text, "regexReplace", location)
    if not isinstance(replacement, str):
        raise EchoTypeError("regexReplace() replacement must be a string", location, code="E2850")
    compiled = _compile(pattern, "regexReplace", location)
    try:
        return compiled.sub(replacement, value)
    except (re.error, IndexError) as exc:
        raise EchoRuntimeError(f"invalid regex replacement: {exc}", location, code="E2850") from exc


def regex_split(text: object, pattern: object, location: SourceLocation | None = None) -> list[str]:
    value = _require_text(text, "regexSplit", location)
    compiled = _compile(pattern, "regexSplit", location)
    return compiled.split(value)
