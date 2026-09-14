from __future__ import annotations

from dataclasses import dataclass

from echo.errors import ArgumentError, EchoRuntimeError, EchoTypeError, SourceLocation
from echo.frontend.ast.nodes import Argument, Expression, FunctionDeclaration, ListLiteral, Parameter, TypeAnnotation
from echo.runtime.context import Environment
from echo.runtime.values import format_type, matches_type, raise_exact_shape_error


@dataclass
class EchoFunction:
    declaration: FunctionDeclaration
    closure: Environment


class ReturnValue(Exception):
    def __init__(self, value: object):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


def bind_arguments(
    function_name: str,
    parameters: list[Parameter],
    raw_args: list[Argument],
    location: SourceLocation | None = None,
) -> dict[str, Expression]:
    positional: list[Expression] = []
    keyword: dict[str, Expression] = {}

    for argument in raw_args:
        if argument.name:
            if argument.name in keyword:
                raise ArgumentError(
                    f"Function '{function_name}' got multiple keyword arguments for '{argument.name}'",
                    location,
                    code="E2201",
                )
            keyword[argument.name] = argument.value
        else:
            positional.append(argument.value)

    names = [parameter.name for parameter in parameters]
    variadic = next((parameter for parameter in parameters if parameter.variadic), None)
    required = [parameter for parameter in parameters if not parameter.variadic]
    extra: list[Expression] = []
    if variadic is None:
        if len(positional) > len(parameters):
            expected = len(parameters)
            noun = "argument" if expected == 1 else "arguments"
            raise ArgumentError(
                f"Function '{function_name}' expected at most {expected} {noun}, got {len(positional)}",
                location,
                code="E2202",
            )
    else:
        extra = positional[len(required) :]
        positional = positional[: len(required)]

    bound: dict[str, Expression] = {}
    for index, parameter in enumerate(required[: len(positional)]):
        bound[parameter.name] = positional[index]

    for name, value in keyword.items():
        if name not in names:
            raise ArgumentError(
                f"Function '{function_name}' got an unexpected keyword argument '{name}'",
                location,
                code="E2203",
            )
        if name in bound or (variadic is not None and name == variadic.name and extra):
            raise ArgumentError(
                f"Function '{function_name}' got multiple values for argument '{name}'",
                location,
                code="E2204",
            )
        bound[name] = value

    for parameter in required:
        if parameter.name in bound:
            continue
        if parameter.default is not None:
            bound[parameter.name] = parameter.default
            continue
        label = (
            "destructuring parameter"
            if parameter.pattern is not None
            else f"parameter '{parameter.name}'"
        )
        raise ArgumentError(
            f"Missing argument for {label} in function '{function_name}'",
            location,
            code="E2205",
        )

    if variadic is not None and variadic.name not in bound:
        loc = location or variadic.location
        bound[variadic.name] = ListLiteral(loc, extra)
    return bound


def check_return(name: str, value: object, return_type: TypeAnnotation | None, location: SourceLocation | None = None) -> None:
    if return_type is None:
        return
    if isinstance(return_type, type(None)):
        return
    from echo.frontend.ast.nodes import TypeName

    if isinstance(return_type, TypeName) and return_type.name == "void":
        if value is not None:
            raise EchoTypeError(f"Function '{name}' is declared as void but returns a value", location, code="E2206")
        return
    raise_exact_shape_error(value, return_type, location)
    if not matches_type(value, return_type):
        raise EchoTypeError(
            f"Function '{name}' must return type {format_type(return_type)}, got {type(value).__name__}",
            location,
            code="E2207",
        )


def undefined_function(name: str, location: SourceLocation | None = None) -> None:
    raise EchoRuntimeError(
        f"Function '{name}' is not defined",
        location,
        help_text="Check that the function is defined with 'fn name(...) { ... }' before calling it.",
        code="E2208",
    )
