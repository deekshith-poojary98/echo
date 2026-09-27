from __future__ import annotations

from datetime import date, datetime

from echo.core.jsonutil import echo_to_json, json_to_echo
from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation


def _yaml(location: SourceLocation | None = None):
    try:
        import yaml
    except ImportError as exc:
        raise EchoRuntimeError(
            "yamlParse/yamlWrite require PyYAML (pip install PyYAML)",
            location,
            code="E2855",
        ) from exc
    return yaml


def parse_yaml(text: object, location: SourceLocation | None = None) -> object:
    if not isinstance(text, str):
        raise EchoTypeError("yamlParse() requires a string", location, code="E2855")
    yaml = _yaml(location)
    try:
        # safe_load and yaml_to_echo both recurse. Alias cycles raise RecursionError
        # in yaml_to_echo unless they are detected first.
        return yaml_to_echo(yaml.safe_load(text), location)
    except yaml.YAMLError as exc:
        reason = str(exc).strip() or "invalid YAML"
        raise EchoRuntimeError(f"Invalid YAML: {reason}", location, code="E2855") from exc
    except RecursionError as exc:
        raise EchoRuntimeError("YAML is nested too deeply", location, code="E2855") from exc


def write_yaml(value: object, location: SourceLocation | None = None) -> str:
    yaml = _yaml(location)
    try:
        payload = echo_to_json(value, location)
    except EchoTypeError as exc:
        raise EchoTypeError(str(exc.message).replace("JSON", "YAML"), location, code="E2855") from exc
    except EchoRuntimeError as exc:
        message = str(exc.message).replace("JSON", "YAML").replace(" as JSON", " as YAML")
        raise EchoRuntimeError(message, location, code="E2855") from exc
    if payload is None:
        return "null"
    try:
        dumped = yaml.safe_dump(
            payload,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    except RecursionError as exc:
        raise EchoRuntimeError(
            "Cannot write a value nested too deeply as YAML",
            location,
            code="E2855",
        ) from exc
    except (TypeError, ValueError) as exc:
        raise EchoRuntimeError("Cannot write value as YAML", location, code="E2855") from exc
    text = dumped if isinstance(dumped, str) else str(dumped)
    if text.endswith("\n...\n"):
        text = text[: -len("\n...\n")]
    elif text.endswith("\n"):
        text = text[:-1]
    return text


def yaml_to_echo(
    raw: object,
    location: SourceLocation | None = None,
    seen: set[int] | None = None,
) -> object:
    if isinstance(raw, datetime):
        return raw.isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    if isinstance(raw, (list, dict)):
        ident = id(raw)
        tracking = set() if seen is None else seen
        if ident in tracking:
            raise EchoRuntimeError("Cannot parse cyclic YAML", location, code="E2855")
        tracking.add(ident)
        try:
            if isinstance(raw, list):
                return [yaml_to_echo(item, location, tracking) for item in raw]
            result = {}
            for key, item in raw.items():
                if not isinstance(key, str):
                    raise EchoRuntimeError("YAML mapping keys must be strings", location, code="E2855")
                result[key] = yaml_to_echo(item, location, tracking)
            return result
        finally:
            tracking.remove(ident)
    try:
        return json_to_echo(raw, location)
    except EchoRuntimeError as exc:
        raise EchoRuntimeError("Unsupported YAML value", location, code="E2855") from exc
