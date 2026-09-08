from __future__ import annotations

from echo.errors import EchoIndexError, EchoRuntimeError, EchoTypeError, SourceLocation
from echo.runtime.values import stringify


def apply_format(template: str, values: list[object], location: SourceLocation | None = None) -> str:
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
            else:
                if not placeholder.isdigit():
                    raise EchoRuntimeError(
                        "format() placeholders must be '{}' or numeric indexes like '{0}'",
                        location,
                        code="E2302",
                    )
                arg_index = int(placeholder)
            if arg_index >= len(values):
                raise EchoIndexError(f"format() placeholder index {arg_index} out of range", location, code="E2303")
            result += stringify(values[arg_index])
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
