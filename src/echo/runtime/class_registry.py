"""Runtime registry of class method signatures for interface matching."""

from __future__ import annotations

from echo.frontend.ast.nodes import FunctionType, InterfaceType

_class_methods: dict[str, dict[str, FunctionType]] = {}


def register_class_methods(class_name: str, methods: dict[str, FunctionType]) -> None:
    _class_methods[class_name] = dict(methods)


def class_methods(class_name: str) -> dict[str, FunctionType]:
    return _class_methods.get(class_name, {})


def class_implements_interface(class_name: str, interface: InterfaceType) -> bool:
    from echo.runtime.values import type_assignable

    actual = class_methods(class_name)
    for name, expected in interface.methods.items():
        method = actual.get(name)
        if method is None or not type_assignable(method, expected):
            return False
    return True


def instance_implements_interface(value: object, interface: InterfaceType) -> bool:
    from echo.runtime.instances import ClassInstance
    from echo.runtime.values import type_assignable

    if not isinstance(value, ClassInstance) or value.record is None:
        return False
    actual = value.record.method_types
    for name, expected in interface.methods.items():
        method = actual.get(name)
        if (
            method is None
            or name in value.record.private_methods
            or not type_assignable(method, expected)
        ):
            return False
    return True


def interface_assignable(actual: InterfaceType, expected: InterfaceType) -> bool:
    """True when `actual` provides every method required by `expected`."""
    from echo.runtime.values import type_assignable

    for name, expected_method in expected.methods.items():
        method = actual.methods.get(name)
        if method is None or not type_assignable(method, expected_method):
            return False
    return True


def class_type_implements_interface(
    methods: dict[str, FunctionType],
    interface: InterfaceType,
    *,
    private_methods: frozenset[str] | set[str] | None = None,
) -> bool:
    from echo.runtime.values import type_assignable

    hidden = private_methods or set()
    for name, expected in interface.methods.items():
        method = methods.get(name)
        if method is None or name in hidden or not type_assignable(method, expected):
            return False
    return True
