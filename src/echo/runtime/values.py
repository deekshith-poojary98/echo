from __future__ import annotations

from echo.errors import EchoTypeError, SourceLocation
from echo.frontend.ast.nodes import FunctionType, ObjectType, TypeAnnotation, TypeName


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
    if _is_echo_function(value):
        return "fn"
    if callable(value):
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
    if expected == "fn":
        return _is_echo_function(value)
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
    if isinstance(type_spec, FunctionType):
        if not _is_echo_function(value):
            return False
        declaration = value.declaration
        params = declaration.parameters
        return function_signature_assignable(
            [parameter.type for parameter in params],
            [parameter.default is not None for parameter in params],
            bool(params) and params[-1].variadic,
            declaration.return_type,
            type_spec,
        )
    return False


def function_signature_assignable(
    param_types: list[TypeAnnotation],
    param_defaults: list[bool],
    variadic: bool,
    return_type: TypeAnnotation | None,
    expected: FunctionType,
) -> bool:
    """True when a function value with this signature can be used as `expected`.

    Trailing defaulted parameters may be omitted from the type. Required
    parameters and variadics must still match. Function types themselves never
    spell defaults.
    """
    if bool(variadic) != bool(expected.variadic):
        return False
    if not _type_compatible(return_type, expected.return_type):
        return False

    actual_types = list(param_types)
    actual_defaults = list(param_defaults)
    expected_types = list(expected.param_types)
    if variadic:
        if not actual_types or not expected_types:
            return False
        if not _type_compatible(actual_types[-1], expected_types[-1]):
            return False
        actual_types = actual_types[:-1]
        actual_defaults = actual_defaults[:-1]
        expected_types = expected_types[:-1]

    if len(expected_types) > len(actual_types):
        return False
    for actual, want in zip(actual_types, expected_types):
        if not _type_compatible(actual, want):
            return False
    for index in range(len(expected_types), len(actual_types)):
        defaulted = actual_defaults[index] if index < len(actual_defaults) else False
        if not defaulted:
            return False
    return True


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
    if isinstance(type_spec, FunctionType):
        params = []
        for index, param_type in enumerate(type_spec.param_types):
            suffix = "..." if type_spec.variadic and index == len(type_spec.param_types) - 1 else ""
            params.append(f"{format_type(param_type)}{suffix}")
        return f"fn({', '.join(params)}) -> {format_type(type_spec.return_type)}"
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
    if _is_echo_function(value):
        name = value.declaration.name
        return "<fn>" if name == "<lambda>" else f"<fn {name}>"
    return str(value)


def _is_echo_function(value: object) -> bool:
    return value.__class__.__name__ == "EchoFunction"


def _same_type(left: TypeAnnotation | None, right: TypeAnnotation | None) -> bool:
    if left is None or right is None:
        return left is right
    if isinstance(left, TypeName) and isinstance(right, TypeName):
        return left.name == right.name
    if isinstance(left, ObjectType) and isinstance(right, ObjectType):
        if left.fields.keys() != right.fields.keys():
            return False
        return all(_same_type(left.fields[name], right.fields[name]) for name in left.fields)
    if isinstance(left, FunctionType) and isinstance(right, FunctionType):
        if left.variadic != right.variadic or len(left.param_types) != len(right.param_types):
            return False
        if not all(_same_type(actual, expected) for actual, expected in zip(left.param_types, right.param_types)):
            return False
        return _same_type(left.return_type, right.return_type)
    return False


def _type_compatible(actual: TypeAnnotation | None, expected: TypeAnnotation | None) -> bool:
    if expected is None:
        return True
    if isinstance(expected, TypeName) and expected.name == "dynamic":
        return True
    if actual is None:
        return isinstance(expected, TypeName) and expected.name in {"dynamic", "void"}
    return _same_type(actual, expected)
