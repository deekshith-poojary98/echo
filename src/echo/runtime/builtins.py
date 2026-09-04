from __future__ import annotations

import time

from echo.core.hashes import ensure, require_hash, take, take_last, wipe
from echo.core.lists import count_of, empty, find, insert_at, pull, push, remove_value, require_list, reverse_list
from echo.core.strings import apply_format, require_string
from echo.errors import ArgumentError, EchoRuntimeError, EchoTypeError, SourceLocation
from echo.runtime.values import echo_type_name, is_truthy, stringify

BUILTIN_NAMES = frozenset(
    {
        "wait",
        "ask",
        "say",
        "asInt",
        "asFloat",
        "asBool",
        "asString",
        "type",
        "trim",
        "upperCase",
        "lowerCase",
        "length",
        "keys",
        "values",
        "reverse",
        "push",
        "empty",
        "clone",
        "countOf",
        "merge",
        "find",
        "insertAt",
        "pull",
        "removeValue",
        "order",
        "wipe",
        "take",
        "take_last",
        "ensure",
        "pairs",
        "default",
        "format",
    }
)

MUTATING_METHODS = frozenset(
    {
        "push",
        "empty",
        "merge",
        "insertAt",
        "pull",
        "removeValue",
        "order",
        "wipe",
        "take",
        "take_last",
        "ensure",
        "reverse",
    }
)

BUILTIN_PARAMS = {
    "ask": ["prompt"],
    "wait": ["seconds"],
    "default": ["fallback"],
    "asInt": ["value"],
    "asFloat": ["value"],
    "asBool": ["value"],
    "asString": ["value"],
    "type": ["value"],
    "push": ["value"],
    "insertAt": ["index", "value"],
    "pull": ["index"],
    "removeValue": ["value"],
    "find": ["value"],
    "countOf": ["value"],
    "order": ["comparator"],
    "merge": ["other"],
    "ensure": ["key", "default"],
    "take": ["key"],
}

STANDALONE_PARAMS = {
    "find": ["items", "value"],
    "countOf": ["items", "value"],
}


def builtin_names() -> frozenset[str]:
    return BUILTIN_NAMES


def builtin_param_count(name: str) -> int | None:
    if name in {"say", "format"}:
        return None
    params = BUILTIN_PARAMS.get(name)
    return len(params) if params is not None else None


STANDALONE_MIN_ARGS = {
    "wait": 1,
    "asInt": 1,
    "asFloat": 1,
    "asBool": 1,
    "asString": 1,
    "type": 1,
    "trim": 1,
    "upperCase": 1,
    "lowerCase": 1,
    "length": 1,
    "keys": 1,
    "values": 1,
    "pairs": 1,
    "reverse": 1,
    "clone": 1,
    "format": 1,
    "default": 2,
    "find": 2,
    "countOf": 2,
}


def standalone_min_args(name: str) -> int | None:
    return STANDALONE_MIN_ARGS.get(name)


def resolve_builtin_args(method: str, args: list, has_target: bool, location: SourceLocation | None = None) -> list:
    has_keyword = any(getattr(arg, "name", None) for arg in args)
    if not has_keyword:
        return args
    if method in {"say", "format"}:
        raise EchoTypeError(f"{method}() does not support keyword arguments", location, code="E2601")
    if not has_target and method in STANDALONE_PARAMS:
        params = STANDALONE_PARAMS[method]
    else:
        params = BUILTIN_PARAMS.get(method)
    if params is None:
        raise EchoTypeError(f"{method}() does not support keyword arguments", location, code="E2601")

    positional = []
    keyword = {}
    for arg in args:
        name = getattr(arg, "name", None)
        if name:
            if name in keyword:
                raise EchoTypeError(f"{method}() got multiple values for argument '{name}'", location, code="E2602")
            if name not in params:
                raise EchoTypeError(f"{method}() got an unexpected keyword argument '{name}'", location, code="E2603")
            keyword[name] = arg
        else:
            positional.append(arg)

    slots = [None] * len(params)
    if len(positional) > len(params):
        raise EchoTypeError(
            f"{method}() expected at most {len(params)} argument(s), got {len(positional)}",
            location,
            code="E2604",
        )
    for index, arg in enumerate(positional):
        slots[index] = arg
    for name, value in keyword.items():
        index = params.index(name)
        if slots[index] is not None:
            raise EchoTypeError(f"{method}() got multiple values for argument '{name}'", location, code="E2602")
        slots[index] = value
    while slots and slots[-1] is None:
        slots.pop()
    for index, slot in enumerate(slots):
        if slot is None:
            raise EchoTypeError(f"{method}() missing argument '{params[index]}'", location, code="E2605")
    return slots


def as_int(value: object, location: SourceLocation | None = None) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, float):
            return int(value)
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise EchoTypeError(f"Cannot convert value to int: {value!r}", location, code="E2606") from exc


def as_float(value: object, location: SourceLocation | None = None) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise EchoTypeError(f"Cannot convert value to float: {value!r}", location, code="E2607") from exc


def as_bool(value: object) -> bool:
    if isinstance(value, (str, list, dict)):
        return bool(len(value))
    return bool(value)


def do_wait(seconds: object, location: SourceLocation | None = None) -> None:
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
        raise ArgumentError("wait() requires a numeric number of seconds", location, code="E2608")
    time.sleep(float(seconds))


def do_clone(value: object, location: SourceLocation | None = None) -> object:
    if isinstance(value, list):
        return value.copy()
    if isinstance(value, dict):
        return value.copy()
    raise EchoTypeError("clone() can only be called on lists or hashes", location, code="E2609")


def do_merge(target: object, other: object, location: SourceLocation | None = None) -> object:
    if isinstance(target, list):
        if not isinstance(other, (list, str)):
            raise EchoTypeError("merge() argument must be a list or string when merging lists", location, code="E2610")
        target.extend(other)
        return target
    if isinstance(target, dict):
        if not isinstance(other, dict):
            raise EchoTypeError("merge() argument must be a hash when merging hashes", location, code="E2611")
        target.update(other)
        return target
    raise EchoTypeError("merge() can only be called on lists or hashes", location, code="E2612")


def do_reverse(value: object, location: SourceLocation | None = None) -> object:
    if isinstance(value, str):
        return value[::-1]
    if isinstance(value, list):
        return reverse_list(value)
    raise EchoTypeError("reverse() can only be called on strings or lists", location, code="E2613")


def do_length(value: object, location: SourceLocation | None = None) -> int:
    if isinstance(value, (str, list, dict)):
        return len(value)
    raise EchoTypeError("length() can only be used on strings, lists, or hashes", location, code="E2614")
