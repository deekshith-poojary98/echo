from __future__ import annotations

import base64
import binascii

from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation


def _require_string(
    value: object,
    method: str,
    what: str,
    location: SourceLocation | None,
) -> str:
    if not isinstance(value, str):
        raise EchoTypeError(f"{method}() {what} must be a string", location, code="E2854")
    return value


def base64_encode(text: object, location: SourceLocation | None = None) -> str:
    raw = _require_string(text, "base64Encode", "text", location)
    try:
        return base64.b64encode(raw.encode("utf-8")).decode("ascii")
    except UnicodeEncodeError as exc:
        # Unpaired surrogates cannot be UTF-8 encoded. CLI / run_source only
        # catch EchoError, so this must not leak UnicodeEncodeError.
        raise EchoRuntimeError(
            "base64Encode() text is not valid Unicode",
            location,
            code="E2854",
        ) from exc


def base64_decode(text: object, location: SourceLocation | None = None) -> str:
    encoded = _require_string(text, "base64Decode", "text", location)
    try:
        return base64.b64decode(encoded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise EchoRuntimeError(f"cannot decode base64: {exc}", location, code="E2854") from exc
