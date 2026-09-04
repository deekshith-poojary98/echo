from __future__ import annotations

from functools import cmp_to_key

from echo.core.hashes import ensure, require_hash, take, take_last, wipe
from echo.core.lists import count_of, empty, find, insert_at, pull, push, remove_value, require_list
from echo.core.strings import apply_format, require_string
from echo.errors import (
    ArgumentError,
    EchoIndexError,
    EchoNameError,
    EchoRuntimeError,
    EchoTypeError,
    SourceLocation,
)
from echo.frontend.ast.nodes import (
    AssignmentStatement,
    BinaryExpression,
    BreakStatement,
    CallExpression,
    CompoundAssignment,
    ContinueStatement,
    ExportDeclaration,
    Expression,
    ExpressionStatement,
    ForStatement,
    ForeachStatement,
    FunctionDeclaration,
    HashLiteral,
    IfStatement,
    ImportDeclaration,
    IndexAssignment,
    IndexExpression,
    ListLiteral,
    LiteralExpression,
    MemberExpression,
    Program,
    ReturnStatement,
    Statement,
    StringInterpolation,
    StringLiteralExpression,
    TypeAliasStatement,
    UnaryExpression,
    UseStatement,
    VariableDeclaration,
    VariableExpression,
    WatchStatement,
    WhileStatement,
)
from echo.frontend.tokens import TokenType
from echo.runtime.builtins import (
    BUILTIN_NAMES,
    MUTATING_METHODS,
    as_bool,
    as_float,
    as_int,
    do_clone,
    do_length,
    do_merge,
    do_reverse,
    do_wait,
    resolve_builtin_args,
)
from echo.runtime.context import Environment
from echo.runtime.functions import BreakSignal, ContinueSignal, EchoFunction, ReturnValue, bind_arguments, check_return, undefined_function
from echo.runtime.operators import binary_op, unary_op
from echo.runtime.values import (
    echo_type_name,
    format_type,
    is_truthy,
    matches_type,
    stringify,
    unescape_string,
    validate_type,
)


class Interpreter:
    def execute(self, program: Program, env: Environment | None = None) -> None:
        self.global_env = env or Environment()
        for statement in program.statements:
            self.execute_statement(statement, self.global_env)

    def execute_statement(self, statement: Statement, env: Environment) -> None:
        if isinstance(statement, TypeAliasStatement):
            return
        if isinstance(statement, ImportDeclaration):
            return
        if isinstance(statement, ExportDeclaration):
            if statement.declaration is not None:
                self.execute_statement(statement.declaration, env)
            return
        if isinstance(statement, VariableDeclaration):
            value = self.evaluate(statement.initializer, env)
            validate_type(statement.name, value, statement.declared_type, statement.location)
            if env.is_watched(statement.name):
                self._watch(statement.name, value, env)
            env.define(statement.name, value, statement.declared_type)
            return
        if isinstance(statement, AssignmentStatement):
            value = self.evaluate(statement.value, env)
            if env.is_watched(statement.name):
                self._watch(statement.name, value, env)
            env.assign(statement.name, value, statement.location)
            return
        if isinstance(statement, CompoundAssignment):
            current = env.get(statement.name, statement.location)
            rhs = self.evaluate(statement.value, env)
            op = {
                TokenType.PLUS_EQUAL: TokenType.PLUS,
                TokenType.MINUS_EQUAL: TokenType.MINUS,
                TokenType.STAR_EQUAL: TokenType.STAR,
                TokenType.SLASH_EQUAL: TokenType.SLASH,
                TokenType.PERCENT_EQUAL: TokenType.PERCENT,
            }[statement.operator.type]
            value = binary_op(op, current, rhs, statement.location)
            if env.is_watched(statement.name):
                self._watch(statement.name, value, env)
            env.assign(statement.name, value, statement.location)
            return
        if isinstance(statement, IndexAssignment):
            env.require_mutable(statement.name, statement.location)
            container = env.get(statement.name, statement.location)
            inner = container
            for index_expr in statement.indices[:-1]:
                key = self.evaluate(index_expr, env)
                inner = self._index(inner, key, statement.location)
            final_key = self.evaluate(statement.indices[-1], env)
            value = self.evaluate(statement.value, env)
            self._index_assign(inner, final_key, value, statement.location)
            if env.is_watched(statement.name):
                self._watch(statement.name, container, env, "modified by index assignment to")
            return
        if isinstance(statement, ExpressionStatement):
            self.evaluate(statement.expression, env)
            return
        if isinstance(statement, IfStatement):
            if is_truthy(self.evaluate(statement.condition, env)):
                self._execute_block(statement.then_branch, Environment(env))
            elif statement.else_branch:
                self._execute_block(statement.else_branch, Environment(env))
            return
        if isinstance(statement, WhileStatement):
            try:
                while is_truthy(self.evaluate(statement.condition, env)):
                    try:
                        self._execute_block(statement.body, Environment(env))
                    except ContinueSignal:
                        continue
            except BreakSignal:
                return
            return
        if isinstance(statement, ForStatement):
            start = self._loop_bound(statement.start, env, statement.location)
            end = self._loop_bound(statement.end, env, statement.location)
            step = self._loop_bound(statement.step, env, statement.location)
            if step == 0:
                raise EchoRuntimeError("for-loop step 'by 0' is not allowed", statement.location, code="E2702")
            i = start
            try:
                while (i <= end if statement.inclusive else i < end) if step > 0 else (i >= end if statement.inclusive else i > end):
                    iter_env = Environment(env)
                    iter_env.define(statement.var, i, statement.var_type)
                    try:
                        self._execute_block(statement.body, iter_env)
                    except ContinueSignal:
                        pass
                    i += step
            except BreakSignal:
                return
            return
        if isinstance(statement, ForeachStatement):
            items = self.evaluate(statement.iterable, env)
            if isinstance(items, dict):
                iterator = items.keys()
            elif isinstance(items, list):
                iterator = items
            else:
                raise EchoTypeError(
                    f"foreach iterable must be a list or hash, got {echo_type_name(items)}",
                    statement.location,
                    code="E2703",
                )
            try:
                for item in iterator:
                    if not matches_type(item, statement.var_type):
                        raise EchoTypeError(
                            f"Loop variable {statement.var} must be of type {format_type(statement.var_type)}",
                            statement.location,
                            code="E2703",
                        )
                    iter_env = Environment(env)
                    iter_env.define(statement.var, item, statement.var_type)
                    try:
                        self._execute_block(statement.body, iter_env)
                    except ContinueSignal:
                        continue
            except BreakSignal:
                return
            return
        if isinstance(statement, FunctionDeclaration):
            env.define_function(statement.name, EchoFunction(statement, env))
            return
        if isinstance(statement, ReturnStatement):
            value = self.evaluate(statement.value, env) if statement.value is not None else None
            raise ReturnValue(value)
        if isinstance(statement, BreakStatement):
            raise BreakSignal()
        if isinstance(statement, ContinueStatement):
            raise ContinueSignal()
        if isinstance(statement, UseStatement):
            for name in statement.names:
                env.import_variable(name, statement.mutable, statement.location)
            return
        if isinstance(statement, WatchStatement):
            for name in statement.names:
                env.watch(name, statement.location)
            return
        raise EchoRuntimeError(f"Unknown statement: {type(statement).__name__}", statement.location, code="E2799")

    def evaluate(self, expression: Expression, env: Environment) -> object:
        if isinstance(expression, LiteralExpression):
            return expression.value
        if isinstance(expression, StringLiteralExpression):
            return unescape_string(expression.value)
        if isinstance(expression, StringInterpolation):
            chunks = []
            for part in expression.parts:
                if isinstance(part, StringLiteralExpression):
                    chunks.append(unescape_string(part.value))
                else:
                    chunks.append(stringify(self.evaluate(part, env)))
            return "".join(chunks)
        if isinstance(expression, VariableExpression):
            if env.is_defined(expression.name):
                return env.get(expression.name, expression.location)
            function = env.resolve_function(expression.name)
            if function is not None:
                return function
            raise EchoNameError(f"Variable '{expression.name}' is not defined", expression.location, code="E2002")
        if isinstance(expression, ListLiteral):
            return [self.evaluate(element, env) for element in expression.elements]
        if isinstance(expression, HashLiteral):
            return {pair.key: self.evaluate(pair.value, env) for pair in expression.pairs}
        if isinstance(expression, BinaryExpression):
            if expression.operator.type == TokenType.AND_AND:
                left = self.evaluate(expression.left, env)
                if not is_truthy(left):
                    return False
                return bool(is_truthy(self.evaluate(expression.right, env)))
            if expression.operator.type == TokenType.OR_OR:
                left = self.evaluate(expression.left, env)
                if is_truthy(left):
                    return True
                return bool(is_truthy(self.evaluate(expression.right, env)))
            left = self.evaluate(expression.left, env)
            right = self.evaluate(expression.right, env)
            return binary_op(expression.operator.type, left, right, expression.location)
        if isinstance(expression, UnaryExpression):
            return unary_op(expression.operator.type, self.evaluate(expression.operand, env), expression.location)
        if isinstance(expression, IndexExpression):
            return self._index(self.evaluate(expression.target, env), self.evaluate(expression.index, env), expression.location)
        if isinstance(expression, MemberExpression):
            raise EchoRuntimeError(
                f"Property access '.{expression.name}' is not supported; use method calls or hash indexing",
                expression.location,
                code="E2704",
            )
        if isinstance(expression, CallExpression):
            return self._call(expression, env)
        raise EchoRuntimeError(f"Unknown expression: {type(expression).__name__}", expression.location, code="E2798")

    def _call(self, expression: CallExpression, env: Environment) -> object:
        callee = expression.callee
        if isinstance(callee, MemberExpression):
            target = self.evaluate(callee.object, env)
            return self._call_builtin(callee.name, expression.arguments, env, target, expression.location, callee.object)
        if isinstance(callee, VariableExpression):
            function = env.resolve_function(callee.name)
            if function is not None:
                return self._call_user_function(function, expression.arguments, env, expression.location)
            if callee.name in BUILTIN_NAMES:
                return self._call_builtin(callee.name, expression.arguments, env, None, expression.location, None)
            undefined_function(callee.name, expression.location)
        raise EchoRuntimeError("Invalid call target", expression.location, code="E2705")

    def _call_user_function(self, function: EchoFunction, raw_args, env: Environment, location: SourceLocation) -> object:
        declaration = function.declaration
        params = [parameter.name for parameter in declaration.parameters]
        bound = bind_arguments(declaration.name, params, raw_args, location)
        new_env = Environment(parent=function.closure, is_function=True)
        new_env.function_name = declaration.name
        for parameter in declaration.parameters:
            value = self.evaluate(bound[parameter.name], env)
            if not matches_type(value, parameter.type):
                raise EchoTypeError(
                    f"Argument '{parameter.name}' in function '{declaration.name}' must be of type "
                    f"{format_type(parameter.type)}, got {echo_type_name(value)}",
                    location,
                    code="E2706",
                )
            new_env.define(parameter.name, value, parameter.type)

        if declaration.inline:
            result = self.evaluate(declaration.body, new_env)  # type: ignore[arg-type]
        else:
            try:
                self._execute_block(declaration.body, new_env)  # type: ignore[arg-type]
                result = None
            except ReturnValue as returned:
                result = returned.value
        check_return(declaration.name, result, declaration.return_type, location)
        return result

    def call_function_with_values(self, function: EchoFunction, values: list[object], location: SourceLocation | None = None) -> object:
        declaration = function.declaration
        if len(values) != len(declaration.parameters):
            raise ArgumentError(
                f"Function '{declaration.name}' expected {len(declaration.parameters)} arguments, got {len(values)}",
                location,
                code="E2707",
            )
        new_env = Environment(parent=function.closure, is_function=True)
        new_env.function_name = declaration.name
        for parameter, value in zip(declaration.parameters, values):
            if not matches_type(value, parameter.type):
                raise EchoTypeError(
                    f"Argument '{parameter.name}' in function '{declaration.name}' must be of type "
                    f"{format_type(parameter.type)}, got {echo_type_name(value)}",
                    location,
                    code="E2706",
                )
            new_env.define(parameter.name, value, parameter.type)
        if declaration.inline:
            result = self.evaluate(declaration.body, new_env)  # type: ignore[arg-type]
        else:
            try:
                self._execute_block(declaration.body, new_env)  # type: ignore[arg-type]
                result = None
            except ReturnValue as returned:
                result = returned.value
        check_return(declaration.name, result, declaration.return_type, location)
        return result

    def _call_builtin(
        self,
        method: str,
        raw_args,
        env: Environment,
        target: object,
        location: SourceLocation,
        target_expr: Expression | None,
    ) -> object:
        args = resolve_builtin_args(method, raw_args, target is not None, location)
        if method in MUTATING_METHODS and isinstance(target_expr, VariableExpression):
            if method != "reverse" or isinstance(target, list):
                env.require_mutable(target_expr.name, location)

        evaluated = [self.evaluate(arg.value, env) for arg in args]
        result = self._dispatch_builtin(method, target, evaluated, env, location)

        if method in MUTATING_METHODS and isinstance(target_expr, VariableExpression) and env.is_watched(target_expr.name):
            self._watch(target_expr.name, env.get(target_expr.name, location), env, f"modified by {method}() to")
        return result

    def _dispatch_builtin(self, method: str, target: object, args: list[object], env: Environment, location: SourceLocation) -> object:
        if method == "say":
            print(" ".join(stringify(value) for value in args))
            return None
        if method == "wait":
            if not args:
                raise ArgumentError("wait() requires a seconds argument", location, code="E2608")
            do_wait(args[0], location)
            return None
        if method == "ask":
            prompt = target if target is not None else (args[0] if args else "")
            return input(str(prompt))
        if method == "asInt":
            return as_int(target if target is not None else _first(args, method, location), location)
        if method == "asFloat":
            return as_float(target if target is not None else _first(args, method, location), location)
        if method == "asBool":
            return as_bool(target if target is not None else _first(args, method, location))
        if method == "asString":
            return stringify(target if target is not None else _first(args, method, location))
        if method == "type":
            return echo_type_name(target if target is not None else _first(args, method, location))
        if method == "default":
            value = target if target is not None else _nth(args, 0, method, location)
            fallback = args[0] if target is not None else _nth(args, 1, method, location)
            return value if is_truthy(value) else fallback
        if method == "trim":
            return require_string(target if target is not None else _first(args, method, location), method, location).strip()
        if method == "upperCase":
            return require_string(target if target is not None else _first(args, method, location), method, location).upper()
        if method == "lowerCase":
            return require_string(target if target is not None else _first(args, method, location), method, location).lower()
        if method == "length":
            return do_length(target if target is not None else _first(args, method, location), location)
        if method == "keys":
            return list(require_hash(target if target is not None else _first(args, method, location), method, location).keys())
        if method == "values":
            return list(require_hash(target if target is not None else _first(args, method, location), method, location).values())
        if method == "pairs":
            value = require_hash(target if target is not None else _first(args, method, location), method, location)
            return [[key, item] for key, item in value.items()]
        if method == "reverse":
            return do_reverse(target if target is not None else _first(args, method, location), location)
        if method == "format":
            if target is not None:
                template = require_string(target, method, location)
                return apply_format(template, args, location)
            if not args:
                raise ArgumentError("format() requires a template string", location, code="E2615")
            template = require_string(args[0], method, location)
            return apply_format(template, args[1:], location)
        if method == "clone":
            return do_clone(target if target is not None else _first(args, method, location), location)
        if method == "countOf":
            collection = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            value = args[0] if target is not None else _nth(args, 1, method, location)
            return count_of(collection, value)
        if method == "find":
            collection = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            value = args[0] if target is not None else _nth(args, 1, method, location)
            return find(collection, value)
        if method == "push":
            return push(require_list(target, method, location), _first(args, method, location))
        if method == "empty":
            return empty(require_list(target, method, location))
        if method == "insertAt":
            return insert_at(require_list(target, method, location), _nth(args, 0, method, location), _nth(args, 1, method, location), location)
        if method == "pull":
            index = args[0] if args else None
            return pull(require_list(target, method, location), index, location)
        if method == "removeValue":
            return remove_value(require_list(target, method, location), _first(args, method, location), location)
        if method == "order":
            return self._order(require_list(target, method, location), args, env, location)
        if method == "merge":
            return do_merge(target, _first(args, method, location), location)
        if method == "wipe":
            return wipe(require_hash(target, method, location))
        if method == "take":
            return take(require_hash(target, method, location), _first(args, method, location), location)
        if method == "take_last":
            return take_last(require_hash(target, method, location), location)
        if method == "ensure":
            return ensure(require_hash(target, method, location), _nth(args, 0, method, location), _nth(args, 1, method, location), location)
        raise EchoRuntimeError(f"Unknown method: {method}", location, code="E2616")

    def _order(self, target: list, args: list[object], env: Environment, location: SourceLocation) -> list:
        if not args:
            try:
                target.sort()
            except TypeError as exc:
                raise EchoTypeError(
                    "order() cannot compare mixed or incomparable values",
                    location,
                    code="E2411",
                ) from exc
            return target
        if len(args) != 1:
            raise ArgumentError("order() accepts either no arguments or a single comparator function", location, code="E2617")
        comparator = args[0]
        if isinstance(comparator, str):
            resolved = env.resolve_function(comparator)
            if resolved is None:
                raise EchoNameError(f"Comparator function '{comparator}' is not defined", location, code="E2618")
            comparator = resolved
        if not isinstance(comparator, EchoFunction):
            raise EchoTypeError("order() comparator must be a function name or function", location, code="E2619")
        if len(comparator.declaration.parameters) != 2:
            raise EchoTypeError(
                f"Comparator function '{comparator.declaration.name}' must take exactly two arguments",
                location,
                code="E2409",
            )

        def compare(left, right):
            result = self.call_function_with_values(comparator, [left, right], location)
            if not isinstance(result, int) or isinstance(result, bool):
                raise EchoTypeError(
                    f"Comparator function '{comparator.declaration.name}' must return int",
                    location,
                    code="E2410",
                )
            return result

        try:
            target.sort(key=cmp_to_key(compare))
        except TypeError as exc:
            raise EchoTypeError(
                "order() cannot compare mixed or incomparable values",
                location,
                code="E2411",
            ) from exc
        return target

    def _loop_bound(self, expression: Expression, env: Environment, location: SourceLocation) -> int:
        value = self.evaluate(expression, env)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EchoTypeError("for-loop bounds must be convertible to int", location, code="E2702")
        return int(value)

    def _index_assign(self, target: object, index: object, value: object, location: SourceLocation) -> None:
        if isinstance(target, dict):
            if not isinstance(index, str):
                raise EchoTypeError(f"Hash key must be a string, got {echo_type_name(index)}", location, code="E2710")
            target[index] = value
            return
        if isinstance(target, list):
            if not isinstance(index, int) or isinstance(index, bool):
                raise EchoTypeError(f"List index must be an integer, got {echo_type_name(index)}", location, code="E2714")
            if index < 0 or index >= len(target):
                raise EchoIndexError(f"List index {index} out of range", location, code="E2715")
            target[index] = value
            return
        raise EchoTypeError(f"Cannot index type {echo_type_name(target)}", location, code="E2716")

    def _index(self, target: object, index: object, location: SourceLocation) -> object:
        try:
            if isinstance(target, dict):
                if not isinstance(index, str):
                    raise EchoTypeError(f"Hash key must be a string, got {echo_type_name(index)}", location, code="E2710")
                if index not in target:
                    raise EchoRuntimeError(f"Key '{index}' not found in hash", location, code="E2711")
                return target[index]
            if isinstance(target, str):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise EchoTypeError(f"String index must be an integer, got {echo_type_name(index)}", location, code="E2712")
                if index < 0 or index >= len(target):
                    raise EchoIndexError(f"String index {index} out of range", location, code="E2713")
                return target[index]
            if isinstance(target, list):
                if not isinstance(index, int) or isinstance(index, bool):
                    raise EchoTypeError(f"List index must be an integer, got {echo_type_name(index)}", location, code="E2714")
                if index < 0 or index >= len(target):
                    raise EchoIndexError(f"List index {index} out of range", location, code="E2715")
                return target[index]
            raise EchoTypeError(f"Cannot index type {echo_type_name(target)}", location, code="E2716")
        except EchoRuntimeError:
            raise

    def _execute_block(self, statements: list[Statement], env: Environment) -> None:
        for statement in statements:
            self.execute_statement(statement, env)

    def _watch(self, name: str, value: object, env: Environment, action: str = "changed to") -> None:
        print(f"WATCH: {name} {action} {value} (in {env.current_function_name()})")


def _first(args: list[object], method: str, location: SourceLocation) -> object:
    return _nth(args, 0, method, location)


def _nth(args: list[object], index: int, method: str, location: SourceLocation) -> object:
    if index >= len(args):
        raise ArgumentError(f"{method}() requires a target or at least one argument", location, code="E2620")
    return args[index]
