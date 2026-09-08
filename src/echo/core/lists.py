from __future__ import annotations

from echo.errors import EchoIndexError, EchoRuntimeError, EchoTypeError, SourceLocation


def require_list(value: object, method: str, location: SourceLocation | None = None) -> list:
    if not isinstance(value, list):
        raise EchoTypeError(f"{method}() can only be called on lists", location, code="E2401")
    return value


def push(target: list, value: object) -> list:
    target.append(value)
    return target


def empty(target: list) -> list:
    target.clear()
    return target


def insert_at(target: list, index: object, value: object, location: SourceLocation | None = None) -> list:
    if not isinstance(index, int) or isinstance(index, bool):
        raise EchoTypeError("insertAt() index must be an integer", location, code="E2402")
    if index < 0 or index > len(target):
        raise EchoIndexError(f"Index {index} out of range for list of length {len(target)}", location, code="E2403")
    target.insert(index, value)
    return target


def pull(target: list, index: object | None = None, location: SourceLocation | None = None) -> object:
    if not target:
        raise EchoIndexError("Cannot pull from empty list", location, code="E2404")
    if index is None:
        return target.pop()
    if not isinstance(index, int) or isinstance(index, bool):
        raise EchoTypeError("pull() index must be an integer", location, code="E2405")
    if index < 0 or index >= len(target):
        raise EchoIndexError(f"Index {index} out of range for list of length {len(target)}", location, code="E2406")
    return target.pop(index)


def remove_value(target: list, value: object, location: SourceLocation | None = None) -> list:
    try:
        target.remove(value)
    except ValueError as exc:
        raise EchoRuntimeError(f"Value {value} not found in list", location, code="E2407") from exc
    return target


def find(target: list, value: object) -> int:
    try:
        return target.index(value)
    except ValueError:
        return -1


def count_of(target: list, value: object) -> int:
    return target.count(value)


def reverse_list(target: list) -> list:
    target.reverse()
    return target


def order(target: list) -> list:
    target.sort()
    return target


def list_contains(target: list, value: object, matches) -> bool:
    return any(matches(item, value) for item in target)


def require_slice_bound(value: object, name: str, location: SourceLocation | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise EchoTypeError(f"slice() {name} must be an integer", location, code="E2812")
    return value


def slice_sequence(value: object, start: object, end: object, location: SourceLocation | None = None) -> object:
    if not isinstance(value, (list, str)):
        raise EchoTypeError("slice() can only be called on lists or strings", location, code="E2812")
    begin = require_slice_bound(start, "start", location)
    finish = require_slice_bound(end, "end", location)
    length = len(value)
    if begin < 0 or begin > length:
        raise EchoIndexError(f"slice() start {begin} out of range for length {length}", location, code="E2812")
    if finish < begin or finish > length:
        raise EchoIndexError(f"slice() end {finish} out of range for length {length}", location, code="E2812")
    return value[begin:finish]
