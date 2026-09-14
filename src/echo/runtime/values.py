from __future__ import annotations

from echo.errors import EchoTypeError, SourceLocation
from echo.frontend.ast.nodes import ClassType, FunctionType, ObjectType, TypeAnnotation, TypeName, UnionType
from echo.runtime.instances import ClassInstance


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
    if isinstance(value, ClassInstance):
        return value.class_name
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
    if isinstance(type_spec, UnionType):
        return any(matches_type(value, member) for member in type_spec.members)
    if isinstance(type_spec, ClassType):
        return isinstance(value, ClassInstance) and value.class_name == type_spec.name
    if isinstance(type_spec, ObjectType):
        if isinstance(value, ClassInstance):
            return False
        if not isinstance(value, dict):
            return False
        for field_name, field_type in type_spec.fields.items():
            if field_name not in value:
                return False
            if not matches_type(value[field_name], field_type):
                return False
        if type_spec.exact:
            for key in value:
                if key not in type_spec.fields:
                    return False
        return True
    if isinstance(type_spec, FunctionType):
        cls = value.__class__.__name__
        if cls == "EchoBuiltin":
            from echo.runtime.builtin_types import builtin_fn_type

            return builtin_fn_assignable(builtin_fn_type(value.name), type_spec)
        if cls == "BoundBuiltin":
            from echo.runtime.builtin_types import builtin_method_fn_type

            return builtin_fn_assignable(builtin_method_fn_type(value.name), type_spec)
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


def builtin_fn_assignable(actual: FunctionType, expected: FunctionType) -> bool:
    """Assignability for a builtin (or bound method) used as a `fn(...)` value.

    Wider than user-fn assignability: `dynamic` parameters and returns match
    more specific types, and a variadic builtin such as `say`
    (`fn(dynamic...) -> void`) is assignable to a fixed-arity type such as
    `fn(str) -> dynamic`.
    """
    if not _builtin_return_compatible(actual.return_type, expected.return_type):
        return False

    actual_types = list(actual.param_types)
    expected_types = list(expected.param_types)
    if actual.variadic:
        rest = actual_types[-1] if actual_types else TypeName(actual.location, "dynamic")
        prefix = actual_types[:-1]
        if expected.variadic:
            if not expected_types:
                return False
            if not _builtin_param_compatible(rest, expected_types[-1]):
                return False
            expected_prefix = expected_types[:-1]
            if len(expected_prefix) < len(prefix):
                return False
            for actual_param, expected_param in zip(prefix, expected_prefix):
                if not _builtin_param_compatible(actual_param, expected_param):
                    return False
            for expected_param in expected_prefix[len(prefix) :]:
                if not _builtin_param_compatible(rest, expected_param):
                    return False
            return True
        if len(expected_types) < len(prefix):
            return False
        for actual_param, expected_param in zip(prefix, expected_types):
            if not _builtin_param_compatible(actual_param, expected_param):
                return False
        for expected_param in expected_types[len(prefix) :]:
            if not _builtin_param_compatible(rest, expected_param):
                return False
        return True
    if expected.variadic:
        return False
    if len(actual_types) != len(expected_types):
        return False
    return all(
        _builtin_param_compatible(actual_param, expected_param)
        for actual_param, expected_param in zip(actual_types, expected_types)
    )


def format_type(type_spec: TypeAnnotation | str | None) -> str:
    if type_spec is None:
        return "dynamic"
    if isinstance(type_spec, str):
        return type_spec
    if isinstance(type_spec, TypeName):
        return type_spec.name
    if isinstance(type_spec, UnionType):
        return " | ".join(format_type(member) for member in type_spec.members)
    if isinstance(type_spec, ObjectType):
        fields = ", ".join(f"{name}: {format_type(field)}" for name, field in type_spec.fields.items())
        inner = "{ " + fields + " }"
        return f"exact {inner}" if type_spec.exact else inner
    if isinstance(type_spec, ClassType):
        return type_spec.name
    if isinstance(type_spec, FunctionType):
        params = []
        for index, param_type in enumerate(type_spec.param_types):
            suffix = "..." if type_spec.variadic and index == len(type_spec.param_types) - 1 else ""
            params.append(f"{format_type(param_type)}{suffix}")
        return f"fn({', '.join(params)}) -> {format_type(type_spec.return_type)}"
    return str(type_spec)


def validate_type(name: str, value: object, expected: TypeAnnotation | str | None, location: SourceLocation | None = None) -> None:
    raise_exact_shape_error(value, expected, location)
    if not matches_type(value, expected):
        raise EchoTypeError(
            f"Cannot assign {echo_type_name(value)} to {format_type(expected)} variable '{name}'",
            location,
            code="E2001",
        )


def raise_exact_shape_error(
    value: object,
    expected: TypeAnnotation | str | None,
    location: SourceLocation | None = None,
) -> None:
    """Raise E3208/E3209 when a hash fails an exact object type's shape.

    Unions do not raise shape errors here; a value that matches no branch
    reports the ordinary type mismatch (E2001) via ``matches_type``.
    """
    if isinstance(expected, UnionType):
        return
    if isinstance(expected, ClassType) and isinstance(value, ClassInstance):
        if value.class_name != expected.name:
            return
        for field_name in expected.fields:
            if field_name not in value.fields:
                raise EchoTypeError(
                    f"Class '{expected.name}' is missing required field '{field_name}'",
                    location,
                    help_text="Class instances require every declared field.",
                    code="E3209",
                )
            raise_exact_shape_error(value.fields[field_name], expected.fields[field_name], location)
        for key in value.fields:
            if key not in expected.fields:
                raise EchoTypeError(
                    f"Class '{expected.name}' does not allow extra field '{key}'",
                    location,
                    help_text="Remove extra fields.",
                    code="E3208",
                )
        return
    if not isinstance(expected, ObjectType) or not isinstance(value, dict):
        return
    for field_name, field_type in expected.fields.items():
        if field_name not in value:
            if expected.exact:
                raise EchoTypeError(
                    f"Exact type {format_type(expected)} is missing required field '{field_name}'",
                    location,
                    help_text="Exact types require every listed field.",
                    code="E3209",
                )
            continue
        raise_exact_shape_error(value[field_name], field_type, location)
    if expected.exact:
        for key in value:
            if key not in expected.fields:
                raise EchoTypeError(
                    f"Exact type {format_type(expected)} does not allow extra field '{key}'",
                    location,
                    help_text="Remove extra fields, or use an open hash type { ... } if extras are allowed.",
                    code="E3208",
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
    if isinstance(value, ClassInstance):
        return True
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
    if isinstance(value, ClassInstance):
        parts = [f"{key}: {stringify(item, True)}" for key, item in value.fields.items()]
        return f"{value.class_name} {{{', '.join(parts)}}}"
    if _is_echo_function(value):
        cls = value.__class__.__name__
        if cls == "EchoFunction":
            name = value.declaration.name
            return "<fn>" if name == "<lambda>" else f"<fn {name}>"
        return f"<fn {value.name}>"
    return str(value)


def _is_echo_function(value: object) -> bool:
    return value.__class__.__name__ in {"EchoFunction", "EchoBuiltin", "BoundBuiltin"}


def _builtin_param_compatible(actual: TypeAnnotation | None, expected: TypeAnnotation | None) -> bool:
    if expected is None or (isinstance(expected, TypeName) and expected.name == "dynamic"):
        return True
    if actual is None or (isinstance(actual, TypeName) and actual.name == "dynamic"):
        return True
    if isinstance(actual, FunctionType) and isinstance(expected, FunctionType):
        if actual.variadic != expected.variadic or len(actual.param_types) != len(expected.param_types):
            return False
        for actual_param, expected_param in zip(actual.param_types, expected.param_types):
            if not _builtin_param_compatible(actual_param, expected_param):
                return False
        return _builtin_return_compatible(actual.return_type, expected.return_type)
    return _same_type(actual, expected)


def _builtin_return_compatible(actual: TypeAnnotation | None, expected: TypeAnnotation | None) -> bool:
    if expected is None or (isinstance(expected, TypeName) and expected.name == "dynamic"):
        return True
    if actual is None or (isinstance(actual, TypeName) and actual.name == "dynamic"):
        return True
    if isinstance(actual, TypeName) and actual.name == "void":
        return isinstance(expected, TypeName) and expected.name in {"void", "dynamic"}
    return _type_compatible(actual, expected)


def _same_type(left: TypeAnnotation | None, right: TypeAnnotation | None) -> bool:
    if left is None or right is None:
        return left is right
    if isinstance(left, TypeName) and isinstance(right, TypeName):
        return left.name == right.name
    if isinstance(left, UnionType) and isinstance(right, UnionType):
        if len(left.members) != len(right.members):
            return False
        return all(
            any(_same_type(member, other) for other in right.members) for member in left.members
        ) and all(
            any(_same_type(other, member) for member in left.members) for other in right.members
        )
    if isinstance(left, ObjectType) and isinstance(right, ObjectType):
        if left.exact != right.exact:
            return False
        if left.fields.keys() != right.fields.keys():
            return False
        return all(_same_type(left.fields[name], right.fields[name]) for name in left.fields)
    if isinstance(left, ClassType) and isinstance(right, ClassType):
        return left.name == right.name
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


def flatten_union_members(members: list[TypeAnnotation]) -> list[TypeAnnotation]:
    """Flatten nested unions and drop duplicate members (first occurrence wins)."""
    flat: list[TypeAnnotation] = []
    for member in members:
        if isinstance(member, UnionType):
            flat.extend(member.members)
        else:
            flat.append(member)
    unique: list[TypeAnnotation] = []
    for member in flat:
        if not any(_same_type(member, existing) for existing in unique):
            unique.append(member)
    return unique


def make_union(location, members: list[TypeAnnotation]) -> TypeAnnotation:
    """Build a union type, or return the sole member when only one remains."""
    unique = flatten_union_members(members)
    if not unique:
        return TypeName(location, "dynamic")
    if len(unique) == 1:
        return unique[0]
    return UnionType(location, unique)


def type_assignable(actual: TypeAnnotation | None, expected: TypeAnnotation | None) -> bool:
    """True when a value of ``actual`` can be used where ``expected`` is required.

    Rules:
    - ``dynamic`` accepts everything.
    - A non-union is assignable to a union if it is assignable to **any** member.
    - A union is assignable to a non-union if **every** member is assignable to it.
    - Union to union: each source member is assignable to some target member.
    - Exact/open object rules follow ``object_type_assignable``.
    """
    if expected is None:
        return True
    if isinstance(expected, TypeName) and expected.name == "dynamic":
        return True
    if actual is None:
        return isinstance(expected, TypeName) and expected.name in {"dynamic", "void"}

    if isinstance(expected, UnionType):
        if isinstance(actual, UnionType):
            return all(
                any(type_assignable(source, target) for target in expected.members)
                for source in actual.members
            )
        return any(type_assignable(actual, member) for member in expected.members)

    if isinstance(actual, UnionType):
        return all(type_assignable(member, expected) for member in actual.members)

    if isinstance(actual, ObjectType) and isinstance(expected, ObjectType):
        return object_type_assignable(actual, expected)

    if isinstance(actual, ClassType) and isinstance(expected, ClassType):
        return actual.name == expected.name

    if isinstance(actual, FunctionType) and isinstance(expected, FunctionType):
        return function_signature_assignable(
            actual.param_types,
            [False] * len(actual.param_types),
            actual.variadic,
            actual.return_type,
            expected,
        )

    return _same_type(actual, expected)


def object_type_assignable(actual: ObjectType, expected: ObjectType) -> bool:
    """True when a value of `actual` can be used where `expected` is required.

    An exact type may be assigned to an open hash with the same or compatible
    required fields. An open hash is not assignable to an exact type.
    """
    if expected.exact and not actual.exact:
        return False
    for name, expected_field in expected.fields.items():
        if name not in actual.fields:
            return False
        actual_field = actual.fields[name]
        if isinstance(actual_field, ObjectType) and isinstance(expected_field, ObjectType):
            if not object_type_assignable(actual_field, expected_field):
                return False
        elif not type_assignable(actual_field, expected_field):
            return False
    if expected.exact and set(actual.fields) != set(expected.fields):
        return False
    return True
