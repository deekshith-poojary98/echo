from __future__ import annotations

import math
import random
import time
from pathlib import Path

from echo.core.hashes import ensure, hash_has, require_hash, take, take_last, wipe
from echo.core.jsonutil import parse_json, write_json
from echo.core.lists import (
    count_of,
    empty,
    find,
    insert_at,
    join_strings,
    list_contains,
    pull,
    push,
    remove_value,
    require_list,
    reverse_list,
    slice_sequence,
)
from echo.core.regexutil import regex_find, regex_match, regex_replace, regex_split
from echo.core.strings import (
    apply_format,
    replace_first_string,
    replace_string,
    require_string,
    split_string,
    string_contains,
    string_ends_with,
    string_index_of,
    string_last_index_of,
    string_pad_end,
    string_pad_start,
    string_repeat,
    string_starts_with,
)
from echo.errors import ArgumentError, EchoExit, EchoRuntimeError, EchoTypeError, SourceLocation
from echo.runtime.functions import EchoBuiltin
from echo.runtime.host import Host
from echo.runtime.operators import echo_equal
from echo.runtime.testing import TestSession
from echo.runtime.values import echo_type_name, is_truthy, stringify

BUILTIN_NAMES = frozenset(
    {
        "wait",
        "ask",
        "say",
        "eprint",
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
        "split",
        "replace",
        "contains",
        "has",
        "slice",
        "args",
        "env",
        "envOr",
        "readFile",
        "readFileOr",
        "writeFile",
        "parseJson",
        "parseJsonOr",
        "writeJson",
        "asIntOr",
        "asFloatOr",
        "join",
        "startsWith",
        "endsWith",
        "indexOf",
        "lastIndexOf",
        "repeat",
        "padStart",
        "padEnd",
        "replaceFirst",
        "regexMatch",
        "regexFind",
        "regexReplace",
        "regexSplit",
        "fileExists",
        "cwd",
        "exit",
        "isDir",
        "listFiles",
        "mkdir",
        "mkdirAll",
        "removeFile",
        "removeTree",
        "copyFile",
        "pathJoin",
        "assert",
        "expect",
        "expectEq",
        "expectNeq",
        "fail",
        "chunk",
        "every",
        "filter",
        "findIndex",
        "flatMap",
        "flatten",
        "forEach",
        "map",
        "mapValues",
        "partition",
        "rangeList",
        "rangeListInclusive",
        "reduce",
        "some",
        "unique",
        "zip",
        "run",
        "now",
        "random",
        "randomInt",
        "readLine",
        "abs",
        "min",
        "max",
        "floor",
        "ceil",
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
    "asIntOr": ["value", "fallback"],
    "asFloatOr": ["value", "fallback"],
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
    "split": ["separator"],
    "replace": ["old", "new"],
    "contains": ["value"],
    "has": ["key"],
    "slice": ["start", "end"],
    "args": [],
    "env": ["name"],
    "envOr": ["name", "fallback"],
    "readFile": ["path"],
    "readFileOr": ["path", "fallback"],
    "writeFile": ["contents"],
    "parseJson": ["text"],
    "parseJsonOr": ["text", "fallback"],
    "writeJson": ["value"],
    "join": ["separator"],
    "startsWith": ["prefix"],
    "endsWith": ["suffix"],
    "indexOf": ["part"],
    "lastIndexOf": ["part"],
    "repeat": ["n"],
    "padStart": ["width", "fill"],
    "padEnd": ["width", "fill"],
    "replaceFirst": ["old", "new"],
    "regexMatch": ["pattern"],
    "regexFind": ["pattern"],
    "regexReplace": ["pattern", "replacement"],
    "regexSplit": ["pattern"],
    "fileExists": ["path"],
    "cwd": [],
    "exit": ["code"],
    "isDir": ["path"],
    "listFiles": ["path"],
    "mkdir": ["path"],
    "mkdirAll": ["path"],
    "removeFile": ["path"],
    "removeTree": ["path"],
    "copyFile": ["dest"],
    "pathJoin": ["part"],
    "assert": ["message"],
    "expect": ["message"],
    "expectEq": ["right", "message"],
    "expectNeq": ["right", "message"],
    "fail": [],
    "chunk": ["size"],
    "every": ["f"],
    "filter": ["f"],
    "findIndex": ["f"],
    "flatMap": ["f"],
    "flatten": [],
    "forEach": ["f"],
    "map": ["f"],
    "mapValues": ["f"],
    "partition": ["f"],
    "rangeList": ["end"],
    "rangeListInclusive": ["end"],
    "reduce": ["init", "f"],
    "some": ["f"],
    "unique": [],
    "zip": ["right"],
    "run": ["args"],
    "now": [],
    "random": [],
    "randomInt": ["max"],
    "readLine": [],
    "abs": ["value"],
    "min": ["other"],
    "max": ["other"],
    "floor": ["value"],
    "ceil": ["value"],
}

STANDALONE_PARAMS = {
    "find": ["items", "value"],
    "countOf": ["items", "value"],
    "split": ["value", "separator"],
    "replace": ["value", "old", "new"],
    "contains": ["items", "value"],
    "has": ["items", "key"],
    "slice": ["items", "start", "end"],
    "writeFile": ["path", "contents"],
    "envOr": ["name", "fallback"],
    "readFileOr": ["path", "fallback"],
    "parseJsonOr": ["text", "fallback"],
    "asIntOr": ["value", "fallback"],
    "asFloatOr": ["value", "fallback"],
    "join": ["items", "separator"],
    "startsWith": ["value", "prefix"],
    "endsWith": ["value", "suffix"],
    "indexOf": ["value", "part"],
    "lastIndexOf": ["value", "part"],
    "repeat": ["value", "n"],
    "padStart": ["value", "width", "fill"],
    "padEnd": ["value", "width", "fill"],
    "replaceFirst": ["value", "old", "new"],
    "regexMatch": ["text", "pattern"],
    "regexFind": ["text", "pattern"],
    "regexReplace": ["text", "pattern", "replacement"],
    "regexSplit": ["text", "pattern"],
    "min": ["a", "b"],
    "max": ["a", "b"],
    "copyFile": ["src", "dest"],
    "assert": ["cond", "message"],
    "expect": ["cond", "message"],
    "expectEq": ["left", "right", "message"],
    "expectNeq": ["left", "right", "message"],
    "fail": ["message"],
    "chunk": ["items", "size"],
    "every": ["items", "f"],
    "filter": ["items", "f"],
    "findIndex": ["items", "f"],
    "flatMap": ["items", "f"],
    "flatten": ["items"],
    "forEach": ["items", "f"],
    "map": ["items", "f"],
    "mapValues": ["items", "f"],
    "partition": ["items", "f"],
    "rangeList": ["start", "end"],
    "rangeListInclusive": ["start", "end"],
    "reduce": ["items", "init", "f"],
    "some": ["items", "f"],
    "unique": ["items"],
    "zip": ["left", "right"],
    "run": ["command", "args"],
    "randomInt": ["min", "max"],
}


_BUILTIN_VALUES = {name: EchoBuiltin(name) for name in BUILTIN_NAMES}


def builtin_names() -> frozenset[str]:
    return BUILTIN_NAMES


def builtin_value(name: str) -> EchoBuiltin:
    value = _BUILTIN_VALUES.get(name)
    if value is None:
        return EchoBuiltin(name)
    return value


def builtin_param_count(name: str) -> int | None:
    if name in {"say", "eprint", "format", "pathJoin"}:
        return None
    params = BUILTIN_PARAMS.get(name)
    return len(params) if params is not None else None


STANDALONE_MIN_ARGS = {
    "wait": 1,
    "asInt": 1,
    "asFloat": 1,
    "asIntOr": 2,
    "asFloatOr": 2,
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
    "split": 2,
    "replace": 3,
    "contains": 2,
    "has": 2,
    "slice": 3,
    "args": 0,
    "env": 1,
    "envOr": 2,
    "readFile": 1,
    "readFileOr": 2,
    "writeFile": 2,
    "parseJson": 1,
    "parseJsonOr": 2,
    "writeJson": 1,
    "join": 2,
    "startsWith": 2,
    "endsWith": 2,
    "indexOf": 2,
    "lastIndexOf": 2,
    "repeat": 2,
    "padStart": 3,
    "padEnd": 3,
    "replaceFirst": 3,
    "regexMatch": 2,
    "regexFind": 2,
    "regexReplace": 3,
    "regexSplit": 2,
    "fileExists": 1,
    "cwd": 0,
    "exit": 1,
    "isDir": 1,
    "listFiles": 1,
    "mkdir": 1,
    "mkdirAll": 1,
    "removeFile": 1,
    "removeTree": 1,
    "copyFile": 2,
    "pathJoin": 2,
    "assert": 2,
    "expect": 2,
    "expectEq": 3,
    "expectNeq": 3,
    "fail": 1,
    "chunk": 2,
    "every": 2,
    "filter": 2,
    "findIndex": 2,
    "flatMap": 2,
    "flatten": 1,
    "forEach": 2,
    "map": 2,
    "mapValues": 2,
    "partition": 2,
    "rangeList": 2,
    "rangeListInclusive": 2,
    "reduce": 3,
    "some": 2,
    "unique": 1,
    "zip": 2,
    "run": 2,
    "now": 0,
    "random": 0,
    "randomInt": 2,
    "readLine": 0,
    "abs": 1,
    "min": 2,
    "max": 2,
    "floor": 1,
    "ceil": 1,
}


def standalone_min_args(name: str) -> int | None:
    return STANDALONE_MIN_ARGS.get(name)


def resolve_builtin_args(method: str, args: list, has_target: bool, location: SourceLocation | None = None) -> list:
    has_keyword = any(getattr(arg, "name", None) for arg in args)
    if not has_keyword:
        return args
    if method in {"say", "eprint", "format", "pathJoin"}:
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


def as_int_or(value: object, fallback: object, location: SourceLocation | None = None) -> object:
    if isinstance(value, bool):
        raise EchoTypeError("Cannot convert bool to int", location, code="E2606")
    try:
        return as_int(value, location)
    except EchoTypeError:
        return fallback


def as_float_or(value: object, fallback: object, location: SourceLocation | None = None) -> object:
    if isinstance(value, bool):
        raise EchoTypeError("Cannot convert bool to float", location, code="E2607")
    try:
        return as_float(value, location)
    except EchoTypeError:
        return fallback


def _is_nonfinite_float(value: object) -> bool:
    return isinstance(value, float) and not math.isfinite(value)


def as_int(value: object, location: SourceLocation | None = None) -> int:
    if isinstance(value, bool):
        raise EchoTypeError("Cannot convert bool to int", location, code="E2606")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EchoTypeError(f"Cannot convert value to int: {value!r}", location, code="E2606")
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        signed = text[0] in "+-" if text else False
        digits = text[1:] if signed else text
        if text == "" or not digits.isdecimal():
            raise EchoTypeError(f"Cannot convert value to int: {value!r}", location, code="E2606")
        try:
            return int(text)
        except ValueError as exc:
            raise EchoTypeError(f"Cannot convert value to int: {value!r}", location, code="E2606") from exc
    raise EchoTypeError(f"Cannot convert value to int: {value!r}", location, code="E2606")


def as_float(value: object, location: SourceLocation | None = None) -> float:
    if isinstance(value, bool):
        raise EchoTypeError("Cannot convert bool to float", location, code="E2607")
    if isinstance(value, (int, float)):
        try:
            result = float(value)
        except OverflowError as exc:
            raise EchoTypeError(f"Cannot convert value to float: {value!r}", location, code="E2607") from exc
        if not math.isfinite(result):
            raise EchoTypeError(f"Cannot convert value to float: {value!r}", location, code="E2607")
        return result
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            raise EchoTypeError(f"Cannot convert value to float: {value!r}", location, code="E2607")
        try:
            result = float(text)
        except ValueError as exc:
            raise EchoTypeError(f"Cannot convert value to float: {value!r}", location, code="E2607") from exc
        if not math.isfinite(result):
            raise EchoTypeError(f"Cannot convert value to float: {value!r}", location, code="E2607")
        return result
    raise EchoTypeError(f"Cannot convert value to float: {value!r}", location, code="E2607")


def as_bool(value: object) -> bool:
    if isinstance(value, (str, list, dict)):
        return bool(len(value))
    return bool(value)


def do_wait(seconds: object, location: SourceLocation | None = None) -> None:
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
        raise ArgumentError("wait() requires a numeric number of seconds", location, code="E2608")
    if _is_nonfinite_float(seconds):
        raise ArgumentError("wait() requires a finite number of seconds", location, code="E2608")
    if seconds < 0:
        raise ArgumentError("wait() requires a non-negative number of seconds", location, code="E2608")
    try:
        duration = float(seconds)
    except OverflowError as exc:
        raise ArgumentError("wait() requires a finite number of seconds", location, code="E2608") from exc
    time.sleep(duration)


def do_clone(
    value: object,
    location: SourceLocation | None = None,
    _memo: dict[int, object] | None = None,
) -> object:
    if isinstance(value, bool) or value is None or isinstance(value, (int, float, str)):
        return value

    if _memo is None:
        _memo = {}
    object_id = id(value)
    cached = _memo.get(object_id)
    if cached is not None:
        return cached

    if isinstance(value, list):
        cloned: list = []
        _memo[object_id] = cloned
        cloned.extend(do_clone(item, location, _memo) for item in value)
        return cloned

    if isinstance(value, dict):
        cloned_hash: dict = {}
        _memo[object_id] = cloned_hash
        for key, item in value.items():
            cloned_hash[key] = do_clone(item, location, _memo)
        return cloned_hash

    from echo.runtime.instances import ClassInstance

    if isinstance(value, ClassInstance):
        fields: dict[str, object] = {}
        cloned_instance = ClassInstance(value.class_name, fields, value.record)
        _memo[object_id] = cloned_instance
        for key, item in value.fields.items():
            fields[key] = do_clone(item, location, _memo)
        return cloned_instance

    raise EchoTypeError(
        "clone() can only be called on lists, hashes, or class instances",
        location,
        code="E2609",
    )


def do_zip(left: object, right: object, location: SourceLocation | None = None) -> list:
    left_list = require_list(left, "zip", location)
    right_list = require_list(right, "zip", location)
    length = min(len(left_list), len(right_list))
    return [[left_list[index], right_list[index]] for index in range(length)]


def do_unique(value: object, location: SourceLocation | None = None) -> list:
    items = require_list(value, "unique", location)
    result: list = []
    for item in items:
        if not any(echo_equal(seen, item) for seen in result):
            result.append(item)
    return result


def do_chunk(value: object, size: object, location: SourceLocation | None = None) -> list:
    items = require_list(value, "chunk", location)
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise EchoTypeError("chunk() size must be an integer >= 1", location, code="E2842")
    if not items:
        return []
    return [items[index : index + size] for index in range(0, len(items), size)]


def do_flatten(value: object, location: SourceLocation | None = None) -> list:
    items = require_list(value, "flatten", location)
    result: list = []
    for item in items:
        if not isinstance(item, list):
            raise EchoTypeError("flatten() elements must be lists", location, code="E2846")
        result.extend(item)
    return result


def require_int_convertible(
    value: object,
    location: SourceLocation | None = None,
    *,
    what: str,
    code: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EchoTypeError(f"{what} must be convertible to int", location, code=code)
    if _is_nonfinite_float(value):
        raise EchoTypeError(f"{what} must be convertible to int", location, code=code)
    return int(value)


def _range_bound(value: object, method: str, location: SourceLocation | None = None) -> int:
    return require_int_convertible(
        value,
        location,
        what=f"{method}() bounds",
        code="E2843",
    )


def do_range_list(
    start: object,
    end: object,
    location: SourceLocation | None = None,
    *,
    inclusive: bool,
    method: str,
) -> list[int]:
    return do_range_values(start, end, 1, location, inclusive=inclusive, method=method)


def do_range_values(
    start: object,
    end: object,
    step: object,
    location: SourceLocation | None = None,
    *,
    inclusive: bool,
    method: str | None = None,
) -> list[int]:
    if method is not None:
        begin = _range_bound(start, method, location)
        finish = _range_bound(end, method, location)
        stride = _range_bound(step, method, location)
    else:
        begin = _loop_bound(start, location)
        finish = _loop_bound(end, location)
        stride = _loop_bound(step, location)
    if stride == 0:
        raise EchoRuntimeError("range step 'by 0' is not allowed", location, code="E2702")
    values: list[int] = []
    index = begin
    while (index <= finish if inclusive else index < finish) if stride > 0 else (
        index >= finish if inclusive else index > finish
    ):
        values.append(index)
        index += stride
    return values


def _loop_bound(value: object, location: SourceLocation | None = None) -> int:
    return require_int_convertible(value, location, what="range bounds", code="E2702")


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


def do_split(value: object, separator: object, location: SourceLocation | None = None) -> list[str]:
    return split_string(require_string(value, "split", location), separator, location)


def do_replace(value: object, old: object, new: object, location: SourceLocation | None = None) -> str:
    return replace_string(require_string(value, "replace", location), old, new, location)


def do_contains(value: object, part: object, location: SourceLocation | None = None) -> bool:
    if isinstance(value, str):
        return string_contains(value, part, location)
    if isinstance(value, list):
        return list_contains(value, part, echo_equal)
    raise EchoTypeError("contains() can only be called on lists or strings", location, code="E2813")


def do_has(value: object, key: object, location: SourceLocation | None = None) -> bool:
    return hash_has(require_hash(value, "has", location), key, location)


def do_slice(value: object, start: object, end: object, location: SourceLocation | None = None) -> object:
    return slice_sequence(value, start, end, location)


def do_args(args: list[object], host: Host, location: SourceLocation | None = None) -> list[str]:
    if args:
        raise ArgumentError("args() takes no arguments", location, code="E2807")
    return host.program_args()


def do_env(name: object, host: Host, location: SourceLocation | None = None) -> str:
    if not isinstance(name, str):
        raise EchoTypeError("env() name must be a string", location, code="E2804")
    mapping = host.environment()
    if name not in mapping:
        raise EchoRuntimeError(f"environment variable '{name}' is not set", location, code="E2804")
    return mapping[name]


def do_env_or(name: object, fallback: object, host: Host, location: SourceLocation | None = None) -> object:
    if not isinstance(name, str):
        raise EchoTypeError("envOr() name must be a string", location, code="E2804")
    mapping = host.environment()
    if name not in mapping:
        return fallback
    return mapping[name]


def do_read_file(path: object, host: Host, location: SourceLocation | None = None) -> str:
    if not host.allow_files:
        raise EchoRuntimeError("readFile() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("readFile() path must be a string", location, code="E2802")
    target = host.resolve_path(path)
    try:
        return target.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise EchoRuntimeError(f"file not found: {path}", location, code="E2802") from exc
    except UnicodeDecodeError as exc:
        raise EchoRuntimeError(f"file is not valid UTF-8: {path}", location, code="E2803") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"cannot read file: {path}", location, code="E2803") from exc


def do_read_file_or(path: object, fallback: object, host: Host, location: SourceLocation | None = None) -> object:
    if not host.allow_files:
        raise EchoRuntimeError("readFileOr() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("readFileOr() path must be a string", location, code="E2802")
    target = host.resolve_path(path)
    try:
        return target.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError, OSError):
        return fallback


def do_write_file(path: object, contents: object, host: Host, location: SourceLocation | None = None) -> None:
    if not host.allow_files:
        raise EchoRuntimeError("writeFile() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("writeFile() path must be a string", location, code="E2803")
    if not isinstance(contents, str):
        raise EchoTypeError("writeFile() contents must be a string", location, code="E2803")
    target = host.resolve_path(path)
    try:
        target.write_text(contents, encoding="utf-8")
    except OSError as exc:
        raise EchoRuntimeError(f"cannot write file: {path}", location, code="E2803") from exc
    return None


def do_parse_json(text: object, location: SourceLocation | None = None) -> object:
    return parse_json(text, location)


def do_parse_json_or(text: object, fallback: object, location: SourceLocation | None = None) -> object:
    if not isinstance(text, str):
        raise EchoTypeError("parseJsonOr() requires a string", location, code="E2805")
    try:
        return parse_json(text, location)
    except EchoRuntimeError:
        return fallback


def do_write_json(value: object, location: SourceLocation | None = None) -> str:
    return write_json(value, location)


def do_join(value: object, separator: object, location: SourceLocation | None = None) -> str:
    return join_strings(require_list(value, "join", location), separator, location)


def do_starts_with(value: object, prefix: object, location: SourceLocation | None = None) -> bool:
    return string_starts_with(require_string(value, "startsWith", location), prefix, location)


def do_ends_with(value: object, suffix: object, location: SourceLocation | None = None) -> bool:
    return string_ends_with(require_string(value, "endsWith", location), suffix, location)


def do_index_of(value: object, part: object, location: SourceLocation | None = None) -> int:
    return string_index_of(require_string(value, "indexOf", location), part, location)


def do_last_index_of(value: object, part: object, location: SourceLocation | None = None) -> int:
    return string_last_index_of(require_string(value, "lastIndexOf", location), part, location)


def do_repeat(value: object, count: object, location: SourceLocation | None = None) -> str:
    return string_repeat(require_string(value, "repeat", location), count, location)


def do_pad_start(value: object, width: object, fill: object, location: SourceLocation | None = None) -> str:
    return string_pad_start(require_string(value, "padStart", location), width, fill, location)


def do_pad_end(value: object, width: object, fill: object, location: SourceLocation | None = None) -> str:
    return string_pad_end(require_string(value, "padEnd", location), width, fill, location)


def do_replace_first(value: object, old: object, new: object, location: SourceLocation | None = None) -> str:
    return replace_first_string(require_string(value, "replaceFirst", location), old, new, location)


def do_regex_match(text: object, pattern: object, location: SourceLocation | None = None) -> bool:
    return regex_match(text, pattern, location)


def do_regex_find(text: object, pattern: object, location: SourceLocation | None = None) -> str | None:
    return regex_find(text, pattern, location)


def do_regex_replace(
    text: object,
    pattern: object,
    replacement: object,
    location: SourceLocation | None = None,
) -> str:
    return regex_replace(text, pattern, replacement, location)


def do_regex_split(text: object, pattern: object, location: SourceLocation | None = None) -> list[str]:
    return regex_split(text, pattern, location)


def do_file_exists(path: object, host: Host, location: SourceLocation | None = None) -> bool:
    if not host.allow_files:
        raise EchoRuntimeError("fileExists() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("fileExists() path must be a string", location, code="E2802")
    return host.file_exists(path)


def do_cwd(args: list[object], host: Host, location: SourceLocation | None = None) -> str:
    if args:
        raise ArgumentError("cwd() takes no arguments", location, code="E2807")
    return str(host.working_directory())


def do_exit(code: object, location: SourceLocation | None = None) -> None:
    if isinstance(code, bool) or not isinstance(code, int):
        raise EchoTypeError("exit() code must be an integer", location, code="E2808")
    raise EchoExit(code)


def do_is_dir(path: object, host: Host, location: SourceLocation | None = None) -> bool:
    if not host.allow_files:
        raise EchoRuntimeError("isDir() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("isDir() path must be a string", location, code="E2802")
    return host.is_dir(path)


def do_list_files(path: object, host: Host, location: SourceLocation | None = None) -> list[str]:
    if not host.allow_files:
        raise EchoRuntimeError("listFiles() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("listFiles() path must be a string", location, code="E2802")
    try:
        return host.list_entries(path)
    except FileNotFoundError as exc:
        raise EchoRuntimeError(f"directory not found: {path}", location, code="E2802") from exc
    except NotADirectoryError as exc:
        raise EchoRuntimeError(f"not a directory: {path}", location, code="E2802") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"cannot list directory: {path}", location, code="E2803") from exc


def do_mkdir(path: object, host: Host, location: SourceLocation | None = None) -> None:
    if not host.allow_files:
        raise EchoRuntimeError("mkdir() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("mkdir() path must be a string", location, code="E2802")
    target = host.resolve_path(path)
    if target.is_file():
        raise EchoRuntimeError(f"file in the way: {path}", location, code="E2803")
    if target.is_dir():
        raise EchoRuntimeError(f"directory already exists: {path}", location, code="E2803")
    try:
        host.mkdir(path)
    except FileNotFoundError as exc:
        raise EchoRuntimeError(f"parent directory not found: {path}", location, code="E2802") from exc
    except FileExistsError as exc:
        if target.is_dir():
            raise EchoRuntimeError(f"directory already exists: {path}", location, code="E2803") from exc
        raise EchoRuntimeError(f"file in the way: {path}", location, code="E2803") from exc
    except NotADirectoryError as exc:
        raise EchoRuntimeError(f"parent directory not found: {path}", location, code="E2802") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"cannot create directory: {path}", location, code="E2803") from exc
    return None


def do_mkdir_all(path: object, host: Host, location: SourceLocation | None = None) -> None:
    if not host.allow_files:
        raise EchoRuntimeError("mkdirAll() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("mkdirAll() path must be a string", location, code="E2802")
    target = host.resolve_path(path)
    if target.is_file():
        raise EchoRuntimeError(f"file in the way: {path}", location, code="E2803")
    try:
        host.mkdir_all(path)
    except FileExistsError as exc:
        raise EchoRuntimeError(f"file in the way: {path}", location, code="E2803") from exc
    except NotADirectoryError as exc:
        raise EchoRuntimeError(f"parent path is not a directory: {path}", location, code="E2802") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"cannot create directory: {path}", location, code="E2803") from exc
    return None


def do_remove_file(path: object, host: Host, location: SourceLocation | None = None) -> None:
    if not host.allow_files:
        raise EchoRuntimeError("removeFile() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("removeFile() path must be a string", location, code="E2802")
    try:
        host.remove_file(path)
    except FileNotFoundError as exc:
        raise EchoRuntimeError(f"file not found: {path}", location, code="E2802") from exc
    except IsADirectoryError as exc:
        raise EchoRuntimeError(f"not a file: {path}", location, code="E2802") from exc
    except PermissionError as exc:
        target = host.resolve_path(path)
        if target.is_dir():
            raise EchoRuntimeError(f"not a file: {path}", location, code="E2802") from exc
        raise EchoRuntimeError(f"cannot remove file: {path}", location, code="E2803") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"cannot remove file: {path}", location, code="E2803") from exc
    return None


def do_remove_tree(path: object, host: Host, location: SourceLocation | None = None) -> None:
    if not host.allow_files:
        raise EchoRuntimeError("removeTree() is not available in this host", location, code="E2801")
    if not isinstance(path, str):
        raise EchoTypeError("removeTree() path must be a string", location, code="E2802")
    try:
        host.remove_tree(path)
    except FileNotFoundError as exc:
        raise EchoRuntimeError(f"path not found: {path}", location, code="E2802") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"cannot remove path: {path}", location, code="E2803") from exc
    return None


def _require_number(value: object, method: str, location: SourceLocation | None = None) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EchoTypeError(f"{method}() requires a number", location, code="E2818")
    return value


def do_abs(value: object, location: SourceLocation | None = None) -> int | float:
    return abs(_require_number(value, "abs", location))


def do_min(left: object, right: object, location: SourceLocation | None = None) -> int | float:
    first = _require_number(left, "min", location)
    second = _require_number(right, "min", location)
    return first if first <= second else second


def do_max(left: object, right: object, location: SourceLocation | None = None) -> int | float:
    first = _require_number(left, "max", location)
    second = _require_number(right, "max", location)
    return first if first >= second else second


def do_floor(value: object, location: SourceLocation | None = None) -> int:
    number = _require_number(value, "floor", location)
    if _is_nonfinite_float(number):
        raise EchoTypeError("floor() requires a finite number", location, code="E2818")
    return math.floor(number)


def do_ceil(value: object, location: SourceLocation | None = None) -> int:
    number = _require_number(value, "ceil", location)
    if _is_nonfinite_float(number):
        raise EchoTypeError("ceil() requires a finite number", location, code="E2818")
    return math.ceil(number)


def do_assert(cond: object, message: object, location: SourceLocation | None = None) -> None:
    if not isinstance(message, str):
        raise EchoTypeError("assert() message must be a string", location, code="E2819")
    if not is_truthy(cond):
        raise EchoRuntimeError(message, location, code="E2819")
    return None


def do_fail(message: object, location: SourceLocation | None = None) -> None:
    if not isinstance(message, str):
        raise EchoTypeError("fail() message must be a string", location, code="E2825")
    raise EchoRuntimeError(message, location, code="E2825")


def _require_expect_message(method: str, message: object, location: SourceLocation | None, code: str) -> str:
    if not isinstance(message, str):
        raise EchoTypeError(f"{method}() message must be a string", location, code=code)
    return message


def _equality_detail(left: object, right: object) -> str:
    return f"expected {stringify(right, True)}, got {stringify(left, True)}"


def do_expect(
    cond: object,
    message: object,
    location: SourceLocation | None = None,
    session: TestSession | None = None,
) -> None:
    text = _require_expect_message("expect", message, location, "E2826")
    if not isinstance(cond, bool):
        raise EchoTypeError("expect() condition must be a bool", location, code="E2826")
    if cond:
        return None
    if session is None:
        raise EchoRuntimeError(text, location, code="E2826")
    session.record("E2826", text, location=location)
    return None


def do_expect_eq(
    left: object,
    right: object,
    message: object,
    location: SourceLocation | None = None,
    session: TestSession | None = None,
) -> None:
    text = _require_expect_message("expectEq", message, location, "E2827")
    if echo_equal(left, right):
        return None
    detail = _equality_detail(left, right)
    if session is None:
        raise EchoRuntimeError(text, location, help_text=detail, code="E2827")
    session.record("E2827", text, detail=detail, location=location)
    return None


def do_expect_neq(
    left: object,
    right: object,
    message: object,
    location: SourceLocation | None = None,
    session: TestSession | None = None,
) -> None:
    text = _require_expect_message("expectNeq", message, location, "E2828")
    if not echo_equal(left, right):
        return None
    detail = f"expected values to differ, both were {stringify(left, True)}"
    if session is None:
        raise EchoRuntimeError(text, location, help_text=detail, code="E2828")
    session.record("E2828", text, detail=detail, location=location)
    return None


def do_copy_file(src: object, dest: object, host: Host, location: SourceLocation | None = None) -> None:
    if not host.allow_files:
        raise EchoRuntimeError("copyFile() is not available in this host", location, code="E2801")
    if not isinstance(src, str):
        raise EchoTypeError("copyFile() src must be a string", location, code="E2802")
    if not isinstance(dest, str):
        raise EchoTypeError("copyFile() dest must be a string", location, code="E2802")
    source = host.resolve_path(src)
    target = host.resolve_path(dest)
    if source.is_dir():
        raise EchoRuntimeError(f"not a file: {src}", location, code="E2802")
    if target.is_dir():
        raise EchoRuntimeError(f"destination is a directory: {dest}", location, code="E2802")
    try:
        host.copy_file(src, dest)
    except FileNotFoundError as exc:
        if not source.exists():
            raise EchoRuntimeError(f"file not found: {src}", location, code="E2802") from exc
        raise EchoRuntimeError(f"parent directory not found: {dest}", location, code="E2802") from exc
    except IsADirectoryError as exc:
        if source.is_dir():
            raise EchoRuntimeError(f"not a file: {src}", location, code="E2802") from exc
        raise EchoRuntimeError(f"destination is a directory: {dest}", location, code="E2802") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"cannot copy file: {src}", location, code="E2803") from exc
    return None


def do_path_join(parts: list[object], location: SourceLocation | None = None) -> str:
    if len(parts) < 2:
        raise ArgumentError("pathJoin() expected at least 2 argument(s)", location, code="E2620")
    strings: list[str] = []
    for part in parts:
        if not isinstance(part, str):
            raise EchoTypeError("pathJoin() arguments must be strings", location, code="E2821")
        strings.append(part)
    return str(Path(strings[0]).joinpath(*strings[1:]))


def do_run(command: object, args: object, host: Host, location: SourceLocation | None = None) -> dict[str, object]:
    if not host.allow_run:
        raise EchoRuntimeError("run() is not available in this host", location, code="E2801")
    if not isinstance(command, str):
        raise EchoTypeError("run() command must be a string", location, code="E2822")
    if not isinstance(args, list):
        raise EchoTypeError("run() args must be a list of strings", location, code="E2822")
    argv: list[str] = []
    for item in args:
        if not isinstance(item, str):
            raise EchoTypeError("run() args must be a list of strings", location, code="E2822")
        argv.append(item)
    try:
        return host.run_process(command, argv)
    except FileNotFoundError as exc:
        raise EchoRuntimeError(f"executable not found: {command}", location, code="E2822") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"cannot run command: {command}", location, code="E2822") from exc


def do_now(args: list[object], location: SourceLocation | None = None) -> int:
    if args:
        raise ArgumentError("now() takes no arguments", location, code="E2807")
    return int(time.time())


def do_random(args: list[object], location: SourceLocation | None = None) -> float:
    if args:
        raise ArgumentError("random() takes no arguments", location, code="E2807")
    return random.random()


def do_random_int(low: object, high: object, location: SourceLocation | None = None) -> int:
    if isinstance(low, bool) or not isinstance(low, int):
        raise EchoTypeError("randomInt() requires integer arguments", location, code="E2823")
    if isinstance(high, bool) or not isinstance(high, int):
        raise EchoTypeError("randomInt() requires integer arguments", location, code="E2823")
    if low > high:
        raise EchoRuntimeError("randomInt() min must be <= max", location, code="E2823")
    return random.randint(low, high)


def do_ask(prompt: object, location: SourceLocation | None = None) -> str:
    try:
        return input(str(prompt))
    except EOFError as exc:
        raise EchoRuntimeError("end of input", location, code="E2824") from exc


def do_read_line(args: list[object], location: SourceLocation | None = None) -> str:
    if args:
        raise ArgumentError("readLine() takes no arguments", location, code="E2807")
    try:
        return input()
    except EOFError as exc:
        raise EchoRuntimeError("end of input", location, code="E2824") from exc
