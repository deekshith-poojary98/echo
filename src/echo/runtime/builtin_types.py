from __future__ import annotations

from echo.errors import SourceLocation
from echo.frontend.ast.nodes import FunctionType, TypeAnnotation, TypeName

_BUILTIN_LOC = SourceLocation(0, 0, "<builtin>")


def _t(name: str) -> TypeName:
    return TypeName(_BUILTIN_LOC, name)


def _fn(params: list[TypeAnnotation], return_type: TypeAnnotation, variadic: bool = False) -> FunctionType:
    return FunctionType(_BUILTIN_LOC, params, return_type, variadic)


_DYN = _t("dynamic")
_INT = _t("int")
_FLOAT = _t("float")
_STR = _t("str")
_BOOL = _t("bool")
_LIST = _t("list")
_HASH = _t("hash")
_VOID = _t("void")
_UNARY_DYN = _fn([_DYN], _DYN)
_UNARY_BOOL = _fn([_DYN], _BOOL)
_UNARY_LIST = _fn([_DYN], _LIST)
_BINARY_DYN = _fn([_DYN, _DYN], _DYN)

VARIADIC_BUILTINS = frozenset({"say", "eprint", "format", "pathJoin"})

_SIGNATURE_OVERRIDES: dict[str, FunctionType] = {
    "say": _fn([_DYN], _VOID, True),
    "eprint": _fn([_DYN], _VOID, True),
    "format": _fn([_DYN], _STR, True),
    "pathJoin": _fn([_DYN], _STR, True),
    "map": _fn([_LIST, _UNARY_DYN], _LIST),
    "filter": _fn([_DYN, _UNARY_BOOL], _DYN),
    "mapValues": _fn([_HASH, _UNARY_DYN], _HASH),
    "flatMap": _fn([_LIST, _UNARY_LIST], _LIST),
    "forEach": _fn([_LIST, _UNARY_DYN], _VOID),
    "reduce": _fn([_LIST, _DYN, _BINARY_DYN], _DYN),
    "some": _fn([_LIST, _UNARY_BOOL], _BOOL),
    "every": _fn([_LIST, _UNARY_BOOL], _BOOL),
    "findIndex": _fn([_LIST, _UNARY_BOOL], _INT),
    "partition": _fn([_LIST, _UNARY_BOOL], _LIST),
    "abs": _fn([_DYN], _DYN),
    "min": _fn([_DYN, _DYN], _DYN),
    "max": _fn([_DYN, _DYN], _DYN),
    "floor": _fn([_DYN], _INT),
    "ceil": _fn([_DYN], _INT),
    "type": _fn([_DYN], _STR),
    "length": _fn([_DYN], _INT),
    "now": _fn([], _INT),
    "random": _fn([], _FLOAT),
    "fail": _fn([_STR], _VOID),
    "assert": _fn([_DYN, _STR], _VOID),
    "expect": _fn([_DYN, _STR], _VOID),
    "expectEq": _fn([_DYN, _DYN, _STR], _VOID),
    "expectNeq": _fn([_DYN, _DYN, _STR], _VOID),
    "args": _fn([], _LIST),
    "cwd": _fn([], _STR),
    "readLine": _fn([], _STR),
    "flatten": _fn([_LIST], _LIST),
    "unique": _fn([_LIST], _LIST),
    "zip": _fn([_LIST, _LIST], _LIST),
    "chunk": _fn([_LIST, _INT], _LIST),
    "rangeList": _fn([_INT, _INT], _LIST),
    "rangeListInclusive": _fn([_INT, _INT], _LIST),
}


def builtin_fn_type(name: str) -> FunctionType:
    override = _SIGNATURE_OVERRIDES.get(name)
    if override is not None:
        return override
    from echo.runtime.builtins import BUILTIN_PARAMS, STANDALONE_MIN_ARGS, STANDALONE_PARAMS

    if name in STANDALONE_PARAMS:
        params = [_DYN] * len(STANDALONE_PARAMS[name])
        return _fn(params, _DYN)
    minimum = STANDALONE_MIN_ARGS.get(name)
    if minimum is not None:
        return _fn([_DYN] * minimum, _DYN)
    extras = BUILTIN_PARAMS.get(name)
    if extras is not None:
        return _fn([_DYN] * (1 + len(extras)), _DYN)
    return _fn([], _DYN)


def builtin_method_fn_type(name: str) -> FunctionType:
    standalone = builtin_fn_type(name)
    if standalone.variadic:
        if name in {"format", "pathJoin"}:
            return _fn([_DYN], standalone.return_type, True)
        return standalone
    if not standalone.param_types:
        return standalone
    return _fn(list(standalone.param_types[1:]), standalone.return_type, False)


def builtin_callback_arity(name: str, *, bound: bool = False) -> int | None:
    """Exact required arity for use as a HOF callback, or None if variadic."""
    signature = builtin_method_fn_type(name) if bound else builtin_fn_type(name)
    if signature.variadic:
        return None
    return len(signature.param_types)
