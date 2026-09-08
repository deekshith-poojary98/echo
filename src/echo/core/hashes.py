from __future__ import annotations

from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation


def require_hash(value: object, method: str, location: SourceLocation | None = None) -> dict:
    if not isinstance(value, dict):
        raise EchoTypeError(f"{method}() can only be called on hashes", location, code="E2501")
    return value


def wipe(target: dict) -> dict:
    target.clear()
    return target


def take(target: dict, key: object, location: SourceLocation | None = None) -> list:
    if not isinstance(key, str):
        raise EchoTypeError("take() key must be a string", location, code="E2502")
    if key not in target:
        raise EchoRuntimeError(f"Key '{key}' not found in hash", location, code="E2503")
    value = target.pop(key)
    return [key, value]


def take_last(target: dict, location: SourceLocation | None = None) -> list:
    if not target:
        raise EchoRuntimeError("Cannot take_last() from empty hash", location, code="E2504")
    key = list(target.keys())[-1]
    value = target.pop(key)
    return [key, value]


def hash_has(target: dict, key: object, location: SourceLocation | None = None) -> bool:
    if not isinstance(key, str):
        raise EchoTypeError("has() key must be a string", location, code="E2506")
    return key in target


def ensure(target: dict, key: object, default: object, location: SourceLocation | None = None) -> object:
    if not isinstance(key, str):
        raise EchoTypeError("ensure() key must be a string", location, code="E2505")
    if key not in target:
        target[key] = default
    return target[key]
