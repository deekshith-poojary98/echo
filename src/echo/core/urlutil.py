from __future__ import annotations

from urllib.parse import quote, unquote, urlencode, urljoin

from echo.errors import EchoTypeError, SourceLocation


def _require_string(value: object, method: str, location: SourceLocation | None) -> str:
    if not isinstance(value, str):
        raise EchoTypeError(f"{method}() requires a string", location, code="E2853")
    return value


def url_encode(text: object, location: SourceLocation | None = None) -> str:
    return quote(_require_string(text, "urlEncode", location), safe="")


def url_decode(text: object, location: SourceLocation | None = None) -> str:
    return unquote(_require_string(text, "urlDecode", location))


def url_join(base: object, path: object, location: SourceLocation | None = None) -> str:
    root = _require_string(base, "urlJoin", location)
    part = _require_string(path, "urlJoin", location)
    return urljoin(root, part)


def url_query(params: object, location: SourceLocation | None = None) -> str:
    if not isinstance(params, dict):
        raise EchoTypeError("urlQuery() requires a hash", location, code="E2853")
    pairs: list[tuple[str, str]] = []
    for key, value in params.items():
        if not isinstance(key, str):
            raise EchoTypeError("urlQuery() keys must be strings", location, code="E2853")
        if not isinstance(value, str):
            raise EchoTypeError("urlQuery() values must be strings", location, code="E2853")
        pairs.append((key, value))
    return urlencode(pairs)
