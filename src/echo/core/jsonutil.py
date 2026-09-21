from __future__ import annotations

import json
import math

from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation


def parse_json(text: object, location: SourceLocation | None = None) -> object:
    if not isinstance(text, str):
        raise EchoTypeError("parseJson() requires a string", location, code="E2805")
    try:
        # json.loads and json_to_echo both recurse; a JSON bomb of nested
        # arrays/objects raises RecursionError instead of JSONDecodeError.
        return json_to_echo(json.loads(text), location)
    except json.JSONDecodeError as exc:
        raise EchoRuntimeError(f"Invalid JSON: {exc.msg}", location, code="E2805") from exc
    except RecursionError as exc:
        raise EchoRuntimeError("JSON is nested too deeply", location, code="E2805") from exc


def write_json(value: object, location: SourceLocation | None = None) -> str:
    try:
        return json.dumps(echo_to_json(value, location), ensure_ascii=False, allow_nan=False)
    except RecursionError as exc:
        raise EchoRuntimeError(
            "Cannot write a value nested too deeply as JSON",
            location,
            code="E2806",
        ) from exc
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


def echo_to_json(value: object, location: SourceLocation | None = None, seen: set[int] | None = None) -> object:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EchoRuntimeError("Cannot write non-finite float as JSON", location, code="E2806")
        return value
    if isinstance(value, (list, dict)):
        ident = id(value)
        tracking = set() if seen is None else seen
        if ident in tracking:
            raise EchoRuntimeError("Cannot write cyclic value as JSON", location, code="E2806")
        tracking.add(ident)
        try:
            if isinstance(value, list):
                return [echo_to_json(item, location, tracking) for item in value]
            return {str(key): echo_to_json(item, location, tracking) for key, item in value.items()}
        finally:
            tracking.remove(ident)
    raise EchoTypeError(
        f"Cannot write {type(value).__name__} as JSON",
        location,
        code="E2806",
    )
