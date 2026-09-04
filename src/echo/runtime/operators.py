from __future__ import annotations

from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation
from echo.frontend.tokens import TokenType
from echo.runtime.values import is_truthy


def binary_op(op: TokenType, left: object, right: object, location: SourceLocation | None = None) -> object:
    try:
        if op == TokenType.PLUS:
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            if isinstance(left, (int, float)) and isinstance(right, (int, float)) and not isinstance(left, bool) and not isinstance(right, bool):
                return left + right
            raise EchoTypeError(
                f"Cannot add {type(left).__name__} and {type(right).__name__}",
                location,
                code="E2101",
            )
        if op == TokenType.MINUS:
            return _numeric(op, left, right, location, lambda a, b: a - b)
        if op == TokenType.STAR:
            return _numeric(op, left, right, location, lambda a, b: a * b)
        if op == TokenType.SLASH:
            _require_number(left, right, location)
            if right == 0:
                raise EchoRuntimeError("integer division by zero" if _both_int(left, right) else "division by zero", location, code="E2102")
            if _both_int(left, right):
                quotient = abs(int(left)) // abs(int(right))
                if (left < 0) != (right < 0):
                    quotient = -quotient
                return quotient
            return left / right  # type: ignore[operator]
        if op == TokenType.PERCENT:
            _require_number(left, right, location)
            if right == 0:
                raise EchoRuntimeError("integer modulo by zero" if _both_int(left, right) else "modulo by zero", location, code="E2103")
            if _both_int(left, right):
                quotient = abs(int(left)) // abs(int(right))
                if (left < 0) != (right < 0):
                    quotient = -quotient
                return int(left) - (quotient * int(right))
            return left % right  # type: ignore[operator]
        if op == TokenType.EQUAL_EQUAL:
            return echo_equal(left, right)
        if op == TokenType.BANG_EQUAL:
            return not echo_equal(left, right)
        if op in {TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL}:
            if not _comparable(left, right):
                raise EchoTypeError(
                    f"Cannot compare {type(left).__name__} and {type(right).__name__}",
                    location,
                    code="E2104",
                )
            if op == TokenType.LESS:
                return left < right  # type: ignore[operator]
            if op == TokenType.GREATER:
                return left > right  # type: ignore[operator]
            if op == TokenType.LESS_EQUAL:
                return left <= right  # type: ignore[operator]
            return left >= right  # type: ignore[operator]
        if op == TokenType.AND_AND:
            return bool(is_truthy(left) and is_truthy(right))
        if op == TokenType.OR_OR:
            return bool(is_truthy(left) or is_truthy(right))
    except EchoRuntimeError:
        raise
    except TypeError as exc:
        raise EchoTypeError(str(exc), location, code="E2104") from exc
    raise EchoRuntimeError(f"Unknown operator: {op.name}", location, code="E2105")


def _comparable(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return True
    return isinstance(left, str) and isinstance(right, str)


def echo_equal(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return left == right


def unary_op(op: TokenType, operand: object, location: SourceLocation | None = None) -> object:
    if op == TokenType.BANG:
        return not is_truthy(operand)
    if op == TokenType.MINUS:
        if isinstance(operand, bool) or not isinstance(operand, (int, float)):
            raise EchoTypeError(f"Unary '-' requires a numeric operand, got {type(operand).__name__}", location, code="E2106")
        return -operand
    raise EchoRuntimeError(f"Unknown unary operator: {op.name}", location, code="E2107")


def _both_int(left: object, right: object) -> bool:
    return isinstance(left, int) and not isinstance(left, bool) and isinstance(right, int) and not isinstance(right, bool)


def _require_number(left: object, right: object, location: SourceLocation | None) -> None:
    if isinstance(left, bool) or isinstance(right, bool) or not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        raise EchoTypeError("Numeric operator requires numeric operands", location, code="E2108")


def _numeric(op: TokenType, left: object, right: object, location: SourceLocation | None, impl) -> object:
    _require_number(left, right, location)
    return impl(left, right)
