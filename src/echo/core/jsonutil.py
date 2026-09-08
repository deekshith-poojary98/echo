from __future__ import annotations

import json
import math

from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation


def parse_json(text: object, location: SourceLocation | None = None) -> object:
    if not isinstance(text, str):
        raise EchoTypeError("parseJson() requires a string", location, code="E2805")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EchoRuntimeError(f"Invalid JSON: {exc.msg}", location, code="E2805") from exc
    return json_to_echo(raw, location)


def write_json(value: object, location: SourceLocation | None = None) -> str:
    try:
        return json.dumps(echo_to_json(value, location), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EchoRuntimeError("Cannot write value as JSON", location, code="E2806") from exc


def json_to_echo(raw: object, location: SourceLocation | None = None) -> object:
    if raw is None or isinstance(raw, (bool, str)):
        return raw
    if isinstance(raw, int) and not isinstance(raw, bool):
        return raw
    if isinstance(raw, float):
        if not math.isfinite(raw):
            raise EchoRuntimeError("JSON number must be finite", location, code="E2806")
        if raw.is_integer():
            return int(raw)
        return raw
    if isinstance(raw, list):
        return [json_to_echo(item, location) for item in raw]
    if isinstance(raw, dict):
        result = {}
        for key, item in raw.items():
            if not isinstance(key, str):
                raise EchoRuntimeError("JSON object keys must be strings", location, code="E2806")
            result[key] = json_to_echo(item, location)
        return result
    raise EchoRuntimeError("Unsupported JSON value", location, code="E2806")


def echo_to_json(value: object, location: SourceLocation | None = None) -> object:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EchoRuntimeError("Cannot write non-finite float as JSON", location, code="E2806")
        return value
    if isinstance(value, list):
        return [echo_to_json(item, location) for item in value]
    if isinstance(value, dict):
        return {str(key): echo_to_json(item, location) for key, item in value.items()}
    raise EchoTypeError(
        f"Cannot write {type(value).__name__} as JSON",
        location,
        code="E2806",
    )
