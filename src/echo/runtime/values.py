from __future__ import annotations

from echo.errors import EchoTypeError, SourceLocation
from echo.frontend.ast.nodes import ObjectType, TypeAnnotation, TypeName


def echo_type_name(value: object) -> str:
    if value is None:
        return "dynamic"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "hash"
    if callable(value) or value.__class__.__name__ == "EchoFunction":
        return "dynamic"
    return "dynamic"


def is_echo_type(value: object, expected: str) -> bool:
    if expected == "dynamic":
        return True
    if expected == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "float":
        return isinstance(value, float)
    if expected == "str":
        return isinstance(value, str)
    if expected == "bool":
        return isinstance(value, bool)
    if expected == "list":
        return isinstance(value, list)
    if expected == "hash":
        return isinstance(value, dict)
    if expected == "void":
        return value is None
    return False


def matches_type(value: object, type_spec: TypeAnnotation | str | None) -> bool:
    if type_spec is None:
        return True
    if isinstance(type_spec, str):
        return is_echo_type(value, type_spec)
    if isinstance(type_spec, TypeName):
        return is_echo_type(value, type_spec.name)
    if isinstance(type_spec, ObjectType):
        if not isinstance(value, dict):
            return False
        for field_name, field_type in type_spec.fields.items():
            if field_name not in value:
                return False
            if not matches_type(value[field_name], field_type):
                return False
        return True
    return False


def format_type(type_spec: TypeAnnotation | str | None) -> str:
    if type_spec is None:
        return "dynamic"
    if isinstance(type_spec, str):
        return type_spec
    if isinstance(type_spec, TypeName):
        return type_spec.name
    if isinstance(type_spec, ObjectType):
        fields = ", ".join(f"{name}: {format_type(field)}" for name, field in type_spec.fields.items())
        return "{ " + fields + " }"
    return str(type_spec)


def validate_type(name: str, value: object, expected: TypeAnnotation | str | None, location: SourceLocation | None = None) -> None:
    if not matches_type(value, expected):
        raise EchoTypeError(
            f"Cannot assign {echo_type_name(value)} to {format_type(expected)} variable '{name}'",
            location,
            code="E2001",
        )


def is_truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, (str, list, dict)):
        return len(value) != 0
    return True


def unescape_string(value: str) -> str:
    result = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            mapping = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "'": "'", "\\": "\\"}
            result.append(mapping.get(nxt, nxt))
            i += 2
            continue
        result.append(value[i])
        i += 1
    return "".join(result)


def quote_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def stringify(value: object, nested: bool = False) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return quote_string(value) if nested else value
    if isinstance(value, list):
        return "[" + ", ".join(stringify(item, True) for item in value) + "]"
    if isinstance(value, dict):
        parts = [f"{stringify(key, True)}: {stringify(item, True)}" for key, item in value.items()]
        return "{" + ", ".join(parts) + "}"
    return str(value)
