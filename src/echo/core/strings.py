from __future__ import annotations

from echo.errors import EchoIndexError, EchoRuntimeError, EchoTypeError, SourceLocation
from echo.runtime.values import stringify


def _is_named_placeholder(placeholder: str) -> bool:
    if not placeholder or not (placeholder[0].isalpha() or placeholder[0] == "_"):
        return False
    return all(ch.isalnum() or ch == "_" for ch in placeholder)


def _split_format_args(
    template: str,
    values: list[object],
    location: SourceLocation | None,
) -> tuple[list[object], dict[object, object] | None]:
    """Positional args plus optional trailing hash for named placeholders."""
    needs_named = False
    i = 0
    while i < len(template):
        if template[i] == "{":
            if i + 1 < len(template) and template[i + 1] == "{":
                i += 2
                continue
            end = template.find("}", i + 1)
            if end == -1:
                break
            placeholder = template[i + 1 : end].strip()
            if placeholder and not placeholder.isdecimal() and _is_named_placeholder(placeholder):
                needs_named = True
                break
            i = end + 1
            continue
        if template[i] == "}" and i + 1 < len(template) and template[i + 1] == "}":
            i += 2
            continue
        i += 1

    if not needs_named:
        return values, None
    if not values or not isinstance(values[-1], dict):
        raise EchoRuntimeError(
            "format() named placeholders require a trailing hash argument",
            location,
            code="E2306",
        )
    return list(values[:-1]), values[-1]


def apply_format(template: str, values: list[object], location: SourceLocation | None = None) -> str:
    positional, named = _split_format_args(template, values, location)
    result = ""
    auto_index = 0
    i = 0
    while i < len(template):
        if template[i] == "{":
            if i + 1 < len(template) and template[i + 1] == "{":
                result += "{"
                i += 2
                continue
            end = template.find("}", i + 1)
            if end == -1:
                raise EchoRuntimeError("format() string is missing a closing '}'", location, code="E2301")
            placeholder = template[i + 1:end].strip()
            if placeholder == "":
                arg_index = auto_index
                auto_index += 1
                if arg_index >= len(positional):
                    raise EchoIndexError(
                        f"format() placeholder index {arg_index} out of range",
                        location,
                        code="E2303",
                    )
                result += stringify(positional[arg_index])
            elif placeholder.isdecimal():
                try:
                    arg_index = int(placeholder)
                except ValueError as exc:
                    raise EchoRuntimeError(
                        "format() placeholders must be '{}', '{0}', or '{name}'",
                        location,
                        code="E2302",
                    ) from exc
                if arg_index >= len(positional):
                    raise EchoIndexError(
                        f"format() placeholder index {arg_index} out of range",
                        location,
                        code="E2303",
                    )
                result += stringify(positional[arg_index])
            elif _is_named_placeholder(placeholder):
                assert named is not None
                if placeholder not in named:
                    raise EchoRuntimeError(
                        f"format() missing named placeholder '{placeholder}'",
                        location,
                        code="E2307",
                    )
                result += stringify(named[placeholder])
            else:
                raise EchoRuntimeError(
                    "format() placeholders must be '{}', '{0}', or '{name}'",
                    location,
                    code="E2302",
                )
            i = end + 1
            continue
        if template[i] == "}":
            if i + 1 < len(template) and template[i + 1] == "}":
                result += "}"
                i += 2
                continue
            raise EchoRuntimeError("format() encountered an unmatched '}'", location, code="E2304")
        result += template[i]
        i += 1
    return result


def require_string(value: object, method: str, location: SourceLocation | None = None) -> str:
    if not isinstance(value, str):
        raise EchoTypeError(f"{method}() can only be called on strings", location, code="E2305")
    return value


def split_string(value: str, separator: object, location: SourceLocation | None = None) -> list[str]:
    if not isinstance(separator, str) or separator == "":
        raise EchoRuntimeError("split() separator must be a non-empty string", location, code="E2810")
    return value.split(separator)


def replace_string(value: str, old: object, new: object, location: SourceLocation | None = None) -> str:
    if not isinstance(old, str) or not isinstance(new, str):
        raise EchoTypeError("replace() requires string arguments", location, code="E2811")
    if old == "":
        raise EchoRuntimeError("replace() search string must be non-empty", location, code="E2811")
    return value.replace(old, new)


def string_contains(value: str, part: object, location: SourceLocation | None = None) -> bool:
    if not isinstance(part, str):
        raise EchoTypeError("contains() on a string requires a string", location, code="E2813")
    return part in value


def string_starts_with(value: str, prefix: object, location: SourceLocation | None = None) -> bool:
    if not isinstance(prefix, str):
        raise EchoTypeError("startsWith() requires a string", location, code="E2814")
    return value.startswith(prefix)


def string_ends_with(value: str, suffix: object, location: SourceLocation | None = None) -> bool:
    if not isinstance(suffix, str):
        raise EchoTypeError("endsWith() requires a string", location, code="E2814")
    return value.endswith(suffix)


def string_index_of(value: str, part: object, location: SourceLocation | None = None) -> int:
    if not isinstance(part, str):
        raise EchoTypeError("indexOf() requires a string", location, code="E2814")
    return value.find(part)


def string_last_index_of(value: str, part: object, location: SourceLocation | None = None) -> int:
    if not isinstance(part, str):
        raise EchoTypeError("lastIndexOf() requires a string", location, code="E2814")
    return value.rfind(part)


def string_repeat(value: str, count: object, location: SourceLocation | None = None) -> str:
    if isinstance(count, bool) or not isinstance(count, int):
        raise EchoTypeError("repeat() count must be an integer", location, code="E2816")
    if count < 0:
        raise EchoRuntimeError("repeat() count must be non-negative", location, code="E2816")
    return value * count


def string_pad_start(value: str, width: object, fill: object, location: SourceLocation | None = None) -> str:
    return _pad_string(value, width, fill, start=True, method="padStart", location=location)


def string_pad_end(value: str, width: object, fill: object, location: SourceLocation | None = None) -> str:
    return _pad_string(value, width, fill, start=False, method="padEnd", location=location)


def _pad_string(
    value: str,
    width: object,
    fill: object,
    *,
    start: bool,
    method: str,
    location: SourceLocation | None,
) -> str:
    if isinstance(width, bool) or not isinstance(width, int):
        raise EchoTypeError(f"{method}() width must be an integer", location, code="E2817")
    if width < 0:
        raise EchoRuntimeError(f"{method}() width must be non-negative", location, code="E2817")
    if not isinstance(fill, str):
        raise EchoTypeError(f"{method}() fill must be a string", location, code="E2817")
    if fill == "":
        raise EchoRuntimeError(f"{method}() fill must be a non-empty string", location, code="E2817")
    if len(value) >= width:
        return value
    needed = width - len(value)
    padding = (fill * ((needed // len(fill)) + 1))[:needed]
    if start:
        return padding + value
    return value + padding


def replace_first_string(value: str, old: object, new: object, location: SourceLocation | None = None) -> str:
    if not isinstance(old, str) or not isinstance(new, str):
        raise EchoTypeError("replaceFirst() requires string arguments", location, code="E2811")
    if old == "":
        raise EchoRuntimeError("replaceFirst() search string must be non-empty", location, code="E2811")
    return value.replace(old, new, 1)
