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
