from __future__ import annotations

import sys
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
    DestructureAssignment,
    DestructureDeclaration,
    ExportDeclaration,
    Expression,
    ExpressionStatement,
    ForStatement,
    ForeachStatement,
    FunctionDeclaration,
    HashLiteral,
    HashPattern,
    IfStatement,
    ImportDeclaration,
    IndexAssignment,
    IndexExpression,
    LambdaExpression,
    ListLiteral,
    ListPattern,
    LiteralExpression,
    LiteralPattern,
    MemberExpression,
    NamePattern,
    Pattern,
    Program,
    RangeExpression,
    ReturnStatement,
    SliceExpression,
    Statement,
    StringInterpolation,
    StringLiteralExpression,
    SwitchStatement,
    TypeAliasStatement,
    TypeName,
    TypePattern,
    UnaryExpression,
    UseStatement,
    VariableDeclaration,
    VariableExpression,
    WatchStatement,
    WhileStatement,
    list_pattern_fixed,
    list_pattern_rest,
)
from echo.frontend.tokens import TokenType
from echo.runtime.builtins import (
    BUILTIN_NAMES,
    MUTATING_METHODS,
    as_bool,
    as_float,
    as_float_or,
    as_int,
    as_int_or,
    builtin_value,
    do_abs,
    do_args,
    do_assert,
    do_ceil,
    do_chunk,
    do_clone,
    do_contains,
    do_copy_file,
    do_cwd,
    do_ends_with,
    do_env,
    do_env_or,
    do_exit,
    do_expect,
    do_expect_eq,
    do_expect_neq,
    do_fail,
    do_file_exists,
    do_flatten,
    do_floor,
    do_has,
    do_index_of,
    do_is_dir,
    do_join,
    do_last_index_of,
    do_length,
    do_list_files,
    do_max,
    do_merge,
    do_min,
    do_mkdir,
    do_now,
    do_pad_end,
    do_pad_start,
    do_parse_json,
    do_parse_json_or,
    do_path_join,
    do_random,
    do_random_int,
    do_range_list,
    do_range_values,
    do_read_file,
    do_read_file_or,
    do_read_line,
    do_remove_file,
    do_repeat,
    do_replace,
    do_replace_first,
    do_reverse,
    do_run,
    do_slice,
    do_split,
    do_starts_with,
    do_unique,
    do_wait,
    do_write_file,
    do_write_json,
    do_zip,
    resolve_builtin_args,
)
from echo.runtime.host import Host
from echo.runtime.context import Environment
from echo.runtime.freeze import freeze, require_unfrozen
from echo.runtime.testing import TestSession
from echo.runtime.functions import (
    BoundBuiltin,
    BreakSignal,
    ContinueSignal,
    EchoBuiltin,
    EchoFunction,
    ReturnValue,
    bind_arguments,
    callable_name,
    check_return,
    is_echo_callable,
    undefined_function,
)
from echo.runtime.operators import binary_op, echo_equal, unary_op
from echo.runtime.values import (
    echo_type_name,
    format_type,
    is_truthy,
    matches_type,
    raise_exact_shape_error,
    stringify,
    unescape_string,
    validate_type,
)


class Interpreter:
    def __init__(self, host: Host | None = None, test_session: TestSession | None = None) -> None:
        self.host = host or Host()
        self.test_session = test_session

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
            if statement.const:
                freeze(value)
            env.define(
                statement.name,
                value,
                statement.declared_type,
                mutable=not statement.const,
                const=statement.const,
            )
            return
        if isinstance(statement, DestructureDeclaration):
            value = self.evaluate(statement.initializer, env)
            self._unpack_pattern(
                statement.pattern,
                value,
                env,
                declare=True,
                const=statement.const,
                location=statement.location,
            )
            return
        if isinstance(statement, DestructureAssignment):
            value = self.evaluate(statement.value, env)
            self._unpack_pattern(
                statement.pattern,
                value,
                env,
                declare=False,
                const=False,
                location=statement.location,
            )
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
        if isinstance(statement, SwitchStatement):
            discriminant = self.evaluate(statement.discriminant, env)
            for arm in statement.arms:
                arm_env = Environment(env)
                if arm.pattern is None or self._try_match_switch_pattern(
                    arm.pattern, discriminant, arm_env, statement.location
                ):
                    self._execute_block(arm.body, arm_env)
                    return
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
                    raise_exact_shape_error(item, statement.var_type, statement.location)
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
            if expression.name in BUILTIN_NAMES:
                return builtin_value(expression.name)
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
        if isinstance(expression, SliceExpression):
            target = self.evaluate(expression.target, env)
            start = self.evaluate(expression.start, env) if expression.start is not None else 0
            if expression.end is not None:
                end = self.evaluate(expression.end, env)
            elif isinstance(target, (list, str)):
                end = len(target)
            else:
                end = 0
            return do_slice(target, start, end, expression.location)
        if isinstance(expression, RangeExpression):
            return do_range_values(
                self.evaluate(expression.start, env),
                self.evaluate(expression.end, env),
                self.evaluate(expression.step, env),
                expression.location,
                inclusive=expression.inclusive,
            )
        if isinstance(expression, LambdaExpression):
            return self._lambda_function(expression, env)
        if isinstance(expression, MemberExpression):
            if expression.name in BUILTIN_NAMES:
                return BoundBuiltin(expression.name, self.evaluate(expression.object, env))
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
            if env.is_defined(callee.name):
                value = env.get(callee.name, expression.location)
                return self._call_value(value, expression.arguments, env, expression.location, callee.name)
            undefined_function(callee.name, expression.location)
        value = self.evaluate(callee, env)
        return self._call_value(value, expression.arguments, env, expression.location, None)

    def _call_value(
        self,
        value: object,
        raw_args,
        env: Environment,
        location: SourceLocation,
        name: str | None,
    ) -> object:
        if isinstance(value, EchoFunction):
            return self._call_user_function(value, raw_args, env, location)
        if isinstance(value, EchoBuiltin):
            return self._call_builtin(value.name, raw_args, env, None, location, None)
        if isinstance(value, BoundBuiltin):
            return self._call_builtin(value.name, raw_args, env, value.receiver, location, None)
        if name is not None:
            raise EchoTypeError(
                f"Cannot call '{name}' because it is not a function",
                location,
                code="E2705",
            )
        raise EchoRuntimeError("Invalid call target", location, code="E2705")

    def _lambda_function(self, expression: LambdaExpression, env: Environment) -> EchoFunction:
        declaration = FunctionDeclaration(
            expression.location,
            "<lambda>",
            expression.parameters,
            expression.body,
            expression.inline,
            expression.return_type,
        )
        return EchoFunction(declaration, env)

    def _call_user_function(self, function: EchoFunction, raw_args, env: Environment, location: SourceLocation) -> object:
        declaration = function.declaration
        bound = bind_arguments(declaration.name, declaration.parameters, raw_args, location)
        new_env = Environment(parent=function.closure, is_function=True)
        new_env.function_name = declaration.name
        for parameter in declaration.parameters:
            value = self.evaluate(bound[parameter.name], new_env if parameter.default is bound[parameter.name] else env)
            if parameter.variadic:
                if not isinstance(value, list):
                    raise EchoTypeError(
                        f"Argument '{parameter.name}' in function '{declaration.name}' must be a list of "
                        f"{format_type(parameter.type)}, got {echo_type_name(value)}",
                        location,
                        code="E2706",
                    )
                for item in value:
                    raise_exact_shape_error(item, parameter.type, location)
                    if not matches_type(item, parameter.type):
                        raise EchoTypeError(
                            f"Argument '{parameter.name}' in function '{declaration.name}' must be a list of "
                            f"{format_type(parameter.type)}, got list",
                            location,
                            code="E2706",
                        )
            else:
                raise_exact_shape_error(value, parameter.type, location)
                if not matches_type(value, parameter.type):
                    label = "destructuring parameter" if parameter.pattern is not None else f"'{parameter.name}'"
                    raise EchoTypeError(
                        f"Argument {label} in function '{declaration.name}' must be of type "
                        f"{format_type(parameter.type)}, got {echo_type_name(value)}",
                        location,
                        code="E2706",
                    )
            if parameter.pattern is not None:
                self._unpack_pattern(parameter.pattern, value, new_env, declare=True, const=False, location=location)
            else:
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

    def call_function_with_values(self, function: object, values: list[object], location: SourceLocation | None = None) -> object:
        if isinstance(function, EchoBuiltin):
            return self._invoke_builtin_values(function.name, None, values, location)
        if isinstance(function, BoundBuiltin):
            return self._invoke_builtin_values(function.name, function.receiver, values, location)
        if not isinstance(function, EchoFunction):
            raise EchoTypeError("Expected a function value", location, code="E2705")
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
            raise_exact_shape_error(value, parameter.type, location)
            if not matches_type(value, parameter.type):
                label = "destructuring parameter" if parameter.pattern is not None else f"'{parameter.name}'"
                raise EchoTypeError(
                    f"Argument {label} in function '{declaration.name}' must be of type "
                    f"{format_type(parameter.type)}, got {echo_type_name(value)}",
                    location,
                    code="E2706",
                )
            if parameter.pattern is not None:
                self._unpack_pattern(parameter.pattern, value, new_env, declare=True, const=False, location=location)
            else:
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
        collection = target if target is not None else (evaluated[0] if evaluated else None)
        if method in MUTATING_METHODS:
            if method != "reverse" or isinstance(collection, list):
                require_unfrozen(collection, location)
        result = self._dispatch_builtin(method, target, evaluated, env, location)

        if method in MUTATING_METHODS and isinstance(target_expr, VariableExpression) and env.is_watched(target_expr.name):
            self._watch(target_expr.name, env.get(target_expr.name, location), env, f"modified by {method}() to")
        return result

    def _invoke_builtin_values(
        self,
        method: str,
        target: object,
        values: list[object],
        location: SourceLocation | None,
    ) -> object:
        env = getattr(self, "global_env", None) or Environment()
        collection = target if target is not None else (values[0] if values else None)
        if method in MUTATING_METHODS:
            if method != "reverse" or isinstance(collection, list):
                require_unfrozen(collection, location)
        return self._dispatch_builtin(method, target, values, env, location or SourceLocation(0, 0))

    def _dispatch_builtin(self, method: str, target: object, args: list[object], env: Environment, location: SourceLocation) -> object:
        if method == "say":
            print(" ".join(stringify(value) for value in args))
            return None
        if method == "eprint":
            print(" ".join(stringify(value) for value in args), file=sys.stderr)
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
        if method == "asIntOr":
            value = target if target is not None else _nth(args, 0, method, location)
            fallback = args[0] if target is not None else _nth(args, 1, method, location)
            return as_int_or(value, fallback, location)
        if method == "asFloatOr":
            value = target if target is not None else _nth(args, 0, method, location)
            fallback = args[0] if target is not None else _nth(args, 1, method, location)
            return as_float_or(value, fallback, location)
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
            return count_of(collection, value, echo_equal)
        if method == "find":
            collection = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            value = args[0] if target is not None else _nth(args, 1, method, location)
            return find(collection, value, echo_equal)
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
            return remove_value(require_list(target, method, location), _first(args, method, location), location, echo_equal)
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
        if method == "split":
            value = target if target is not None else _nth(args, 0, method, location)
            separator = args[0] if target is not None else _nth(args, 1, method, location)
            return do_split(value, separator, location)
        if method == "replace":
            value = target if target is not None else _nth(args, 0, method, location)
            old = args[0] if target is not None else _nth(args, 1, method, location)
            new = args[1] if target is not None else _nth(args, 2, method, location)
            return do_replace(value, old, new, location)
        if method == "contains":
            value = target if target is not None else _nth(args, 0, method, location)
            part = args[0] if target is not None else _nth(args, 1, method, location)
            return do_contains(value, part, location)
        if method == "has":
            value = target if target is not None else _nth(args, 0, method, location)
            key = args[0] if target is not None else _nth(args, 1, method, location)
            return do_has(value, key, location)
        if method == "slice":
            value = target if target is not None else _nth(args, 0, method, location)
            start = args[0] if target is not None else _nth(args, 1, method, location)
            end = args[1] if target is not None else _nth(args, 2, method, location)
            return do_slice(value, start, end, location)
        if method == "args":
            if target is not None:
                raise ArgumentError("args() takes no arguments", location, code="E2807")
            return do_args(args, self.host, location)
        if method == "env":
            return do_env(target if target is not None else _first(args, method, location), self.host, location)
        if method == "envOr":
            name = target if target is not None else _nth(args, 0, method, location)
            fallback = args[0] if target is not None else _nth(args, 1, method, location)
            return do_env_or(name, fallback, self.host, location)
        if method == "readFile":
            return do_read_file(target if target is not None else _first(args, method, location), self.host, location)
        if method == "readFileOr":
            path = target if target is not None else _nth(args, 0, method, location)
            fallback = args[0] if target is not None else _nth(args, 1, method, location)
            return do_read_file_or(path, fallback, self.host, location)
        if method == "writeFile":
            path = target if target is not None else _nth(args, 0, method, location)
            contents = args[0] if target is not None else _nth(args, 1, method, location)
            return do_write_file(path, contents, self.host, location)
        if method == "parseJson":
            return do_parse_json(target if target is not None else _first(args, method, location), location)
        if method == "parseJsonOr":
            text = target if target is not None else _nth(args, 0, method, location)
            fallback = args[0] if target is not None else _nth(args, 1, method, location)
            return do_parse_json_or(text, fallback, location)
        if method == "writeJson":
            return do_write_json(target if target is not None else _first(args, method, location), location)
        if method == "join":
            value = target if target is not None else _nth(args, 0, method, location)
            separator = args[0] if target is not None else _nth(args, 1, method, location)
            return do_join(value, separator, location)
        if method == "startsWith":
            value = target if target is not None else _nth(args, 0, method, location)
            prefix = args[0] if target is not None else _nth(args, 1, method, location)
            return do_starts_with(value, prefix, location)
        if method == "endsWith":
            value = target if target is not None else _nth(args, 0, method, location)
            suffix = args[0] if target is not None else _nth(args, 1, method, location)
            return do_ends_with(value, suffix, location)
        if method == "indexOf":
            value = target if target is not None else _nth(args, 0, method, location)
            part = args[0] if target is not None else _nth(args, 1, method, location)
            return do_index_of(value, part, location)
        if method == "lastIndexOf":
            value = target if target is not None else _nth(args, 0, method, location)
            part = args[0] if target is not None else _nth(args, 1, method, location)
            return do_last_index_of(value, part, location)
        if method == "repeat":
            value = target if target is not None else _nth(args, 0, method, location)
            count = args[0] if target is not None else _nth(args, 1, method, location)
            return do_repeat(value, count, location)
        if method == "padStart":
            value = target if target is not None else _nth(args, 0, method, location)
            width = args[0] if target is not None else _nth(args, 1, method, location)
            fill = args[1] if target is not None else _nth(args, 2, method, location)
            return do_pad_start(value, width, fill, location)
        if method == "padEnd":
            value = target if target is not None else _nth(args, 0, method, location)
            width = args[0] if target is not None else _nth(args, 1, method, location)
            fill = args[1] if target is not None else _nth(args, 2, method, location)
            return do_pad_end(value, width, fill, location)
        if method == "replaceFirst":
            value = target if target is not None else _nth(args, 0, method, location)
            old = args[0] if target is not None else _nth(args, 1, method, location)
            new = args[1] if target is not None else _nth(args, 2, method, location)
            return do_replace_first(value, old, new, location)
        if method == "fileExists":
            return do_file_exists(target if target is not None else _first(args, method, location), self.host, location)
        if method == "cwd":
            if target is not None:
                raise ArgumentError("cwd() takes no arguments", location, code="E2807")
            return do_cwd(args, self.host, location)
        if method == "exit":
            do_exit(target if target is not None else _first(args, method, location), location)
            return None
        if method == "isDir":
            return do_is_dir(target if target is not None else _first(args, method, location), self.host, location)
        if method == "listFiles":
            return do_list_files(target if target is not None else _first(args, method, location), self.host, location)
        if method == "mkdir":
            return do_mkdir(target if target is not None else _first(args, method, location), self.host, location)
        if method == "removeFile":
            return do_remove_file(target if target is not None else _first(args, method, location), self.host, location)
        if method == "abs":
            return do_abs(target if target is not None else _first(args, method, location), location)
        if method == "min":
            left = target if target is not None else _nth(args, 0, method, location)
            right = args[0] if target is not None else _nth(args, 1, method, location)
            return do_min(left, right, location)
        if method == "max":
            left = target if target is not None else _nth(args, 0, method, location)
            right = args[0] if target is not None else _nth(args, 1, method, location)
            return do_max(left, right, location)
        if method == "floor":
            return do_floor(target if target is not None else _first(args, method, location), location)
        if method == "ceil":
            return do_ceil(target if target is not None else _first(args, method, location), location)
        if method == "assert":
            cond = target if target is not None else _nth(args, 0, method, location)
            message = args[0] if target is not None else _nth(args, 1, method, location)
            return do_assert(cond, message, location)
        if method == "expect":
            cond = target if target is not None else _nth(args, 0, method, location)
            message = args[0] if target is not None else _nth(args, 1, method, location)
            return do_expect(cond, message, location, self.test_session)
        if method == "expectEq":
            left = target if target is not None else _nth(args, 0, method, location)
            right = args[0] if target is not None else _nth(args, 1, method, location)
            message = args[1] if target is not None else _nth(args, 2, method, location)
            return do_expect_eq(left, right, message, location, self.test_session)
        if method == "expectNeq":
            left = target if target is not None else _nth(args, 0, method, location)
            right = args[0] if target is not None else _nth(args, 1, method, location)
            message = args[1] if target is not None else _nth(args, 2, method, location)
            return do_expect_neq(left, right, message, location, self.test_session)
        if method == "fail":
            return do_fail(target if target is not None else _first(args, method, location), location)
        if method == "map":
            items = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            return self._map(items, callback, location)
        if method == "mapValues":
            items = require_hash(target if target is not None else _nth(args, 0, method, location), method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            return self._mapValues(items, callback, location)
        if method == "filter":
            items = target if target is not None else _nth(args, 0, method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            if isinstance(items, list):
                return self._filter(items, callback, location)
            if isinstance(items, dict):
                return self._filter_hash(items, callback, location)
            raise EchoTypeError("filter() can only be called on lists or hashes", location, code="E2401")
        if method == "flatMap":
            items = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            return self._flatMap(items, callback, location)
        if method == "forEach":
            items = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            return self._forEach(items, callback, location)
        if method == "reduce":
            items = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            init = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            callback = _nth(args, 1, method, location) if target is not None else _nth(args, 2, method, location)
            return self._reduce(items, init, callback, location)
        if method == "some":
            items = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            return self._some(items, callback, location)
        if method == "every":
            items = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            return self._every(items, callback, location)
        if method == "findIndex":
            items = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            return self._findIndex(items, callback, location)
        if method == "zip":
            left = target if target is not None else _nth(args, 0, method, location)
            right = args[0] if target is not None else _nth(args, 1, method, location)
            return do_zip(left, right, location)
        if method == "unique":
            return do_unique(target if target is not None else _first(args, method, location), location)
        if method == "flatten":
            return do_flatten(target if target is not None else _first(args, method, location), location)
        if method == "partition":
            items = require_list(target if target is not None else _nth(args, 0, method, location), method, location)
            callback = _nth(args, 0, method, location) if target is not None else _nth(args, 1, method, location)
            return self._partition(items, callback, location)
        if method == "chunk":
            items = target if target is not None else _nth(args, 0, method, location)
            size = args[0] if target is not None else _nth(args, 1, method, location)
            return do_chunk(items, size, location)
        if method == "rangeList":
            start = target if target is not None else _nth(args, 0, method, location)
            end = args[0] if target is not None else _nth(args, 1, method, location)
            return do_range_list(start, end, location, inclusive=False, method=method)
        if method == "rangeListInclusive":
            start = target if target is not None else _nth(args, 0, method, location)
            end = args[0] if target is not None else _nth(args, 1, method, location)
            return do_range_list(start, end, location, inclusive=True, method=method)
        if method == "copyFile":
            src = target if target is not None else _nth(args, 0, method, location)
            dest = args[0] if target is not None else _nth(args, 1, method, location)
            return do_copy_file(src, dest, self.host, location)
        if method == "pathJoin":
            parts = ([target] if target is not None else []) + list(args)
            return do_path_join(parts, location)
        if method == "run":
            command = target if target is not None else _nth(args, 0, method, location)
            argv = args[0] if target is not None else _nth(args, 1, method, location)
            return do_run(command, argv, self.host, location)
        if method == "now":
            if target is not None:
                raise ArgumentError("now() takes no arguments", location, code="E2807")
            return do_now(args, location)
        if method == "random":
            if target is not None:
                raise ArgumentError("random() takes no arguments", location, code="E2807")
            return do_random(args, location)
        if method == "randomInt":
            low = target if target is not None else _nth(args, 0, method, location)
            high = args[0] if target is not None else _nth(args, 1, method, location)
            return do_random_int(low, high, location)
        if method == "readLine":
            if target is not None:
                raise ArgumentError("readLine() takes no arguments", location, code="E2807")
            return do_read_line(args, location)
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
        if not is_echo_callable(comparator):
            raise EchoTypeError("order() comparator must be a function name or function", location, code="E2619")
        if not self._callable_has_arity(comparator, 2):
            raise EchoTypeError(
                f"Comparator function '{callable_name(comparator)}' must take exactly two arguments",
                location,
                code="E2409",
            )

        def compare(left, right):
            result = self.call_function_with_values(comparator, [left, right], location)
            if not isinstance(result, int) or isinstance(result, bool):
                raise EchoTypeError(
                    f"Comparator function '{callable_name(comparator)}' must return int",
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

    def _callable_has_arity(self, callback: object, arity: int) -> bool:
        if isinstance(callback, EchoFunction):
            return len(callback.declaration.parameters) == arity
        from echo.runtime.builtin_types import builtin_callback_arity

        if isinstance(callback, EchoBuiltin):
            actual = builtin_callback_arity(callback.name, bound=False)
        elif isinstance(callback, BoundBuiltin):
            actual = builtin_callback_arity(callback.name, bound=True)
        else:
            return False
        return actual == arity

    def _require_callback(
        self,
        method: str,
        callback: object,
        location: SourceLocation,
        arity: int,
        not_fn_code: str,
        arity_code: str,
    ) -> object:
        if not is_echo_callable(callback):
            raise EchoTypeError(f"{method}() callback must be a function", location, code=not_fn_code)
        if not self._callable_has_arity(callback, arity):
            expected = {1: "one argument", 2: "two arguments"}.get(arity, f"{arity} arguments")
            raise EchoTypeError(
                f"{method}() callback '{callable_name(callback)}' must take exactly {expected}",
                location,
                code=arity_code,
            )
        return callback

    def _require_unary_callback(self, method: str, callback: object, location: SourceLocation) -> object:
        return self._require_callback(method, callback, location, 1, "E2829", "E2830")

    def _map(self, items: list, callback: object, location: SourceLocation) -> list:
        function = self._require_unary_callback("map", callback, location)
        return [self.call_function_with_values(function, [item], location) for item in list(items)]

    def _mapValues(self, items: dict, callback: object, location: SourceLocation) -> dict:
        function = self._require_callback("mapValues", callback, location, 1, "E2844", "E2845")
        return {key: self.call_function_with_values(function, [value], location) for key, value in items.items()}

    def _filter(self, items: list, callback: object, location: SourceLocation) -> list:
        function = self._require_unary_callback("filter", callback, location)
        kept: list[object] = []
        for item in list(items):
            keep = self.call_function_with_values(function, [item], location)
            if not isinstance(keep, bool):
                raise EchoTypeError(
                    f"filter() callback '{callable_name(function)}' must return bool",
                    location,
                    code="E2831",
                )
            if keep is True:
                kept.append(item)
        return kept

    def _filter_hash(self, items: dict, callback: object, location: SourceLocation) -> dict:
        function = self._require_unary_callback("filter", callback, location)
        kept: dict = {}
        for key, value in items.items():
            keep = self.call_function_with_values(function, [value], location)
            if not isinstance(keep, bool):
                raise EchoTypeError(
                    f"filter() callback '{callable_name(function)}' must return bool",
                    location,
                    code="E2831",
                )
            if keep is True:
                kept[key] = value
        return kept

    def _flatMap(self, items: list, callback: object, location: SourceLocation) -> list:
        function = self._require_callback("flatMap", callback, location, 1, "E2837", "E2838")
        flattened: list[object] = []
        for item in list(items):
            mapped = self.call_function_with_values(function, [item], location)
            if not isinstance(mapped, list):
                raise EchoTypeError(
                    f"flatMap() callback '{callable_name(function)}' must return list",
                    location,
                    code="E2839",
                )
            flattened.extend(mapped)
        return flattened

    def _forEach(self, items: list, callback: object, location: SourceLocation) -> None:
        function = self._require_callback("forEach", callback, location, 1, "E2835", "E2836")
        for item in list(items):
            self.call_function_with_values(function, [item], location)
        return None

    def _bool_predicate(self, method: str, function: object, item: object, location: SourceLocation) -> bool:
        matched = self.call_function_with_values(function, [item], location)
        if not isinstance(matched, bool):
            raise EchoTypeError(
                f"{method}() callback '{callable_name(function)}' must return bool",
                location,
                code="E2831",
            )
        return matched

    def _some(self, items: list, callback: object, location: SourceLocation) -> bool:
        function = self._require_callback("some", callback, location, 1, "E2840", "E2841")
        for item in list(items):
            if self._bool_predicate("some", function, item, location) is True:
                return True
        return False

    def _every(self, items: list, callback: object, location: SourceLocation) -> bool:
        function = self._require_callback("every", callback, location, 1, "E2840", "E2841")
        for item in list(items):
            if self._bool_predicate("every", function, item, location) is not True:
                return False
        return True

    def _findIndex(self, items: list, callback: object, location: SourceLocation) -> int:
        function = self._require_callback("findIndex", callback, location, 1, "E2840", "E2841")
        for index, item in enumerate(list(items)):
            if self._bool_predicate("findIndex", function, item, location) is True:
                return index
        return -1

    def _partition(self, items: list, callback: object, location: SourceLocation) -> list:
        function = self._require_callback("partition", callback, location, 1, "E2847", "E2848")
        matches: list[object] = []
        rest: list[object] = []
        for item in list(items):
            if self._bool_predicate("partition", function, item, location) is True:
                matches.append(item)
            else:
                rest.append(item)
        return [matches, rest]

    def _reduce(self, items: list, init: object, callback: object, location: SourceLocation) -> object:
        function = self._require_callback("reduce", callback, location, 2, "E2832", "E2833")
        accumulator = init
        expected = echo_type_name(init)
        for item in list(items):
            accumulator = self.call_function_with_values(function, [accumulator, item], location)
            if expected != "dynamic" and echo_type_name(accumulator) != expected:
                raise EchoTypeError(
                    f"reduce() callback '{callable_name(function)}' must return {expected}, "
                    f"got {echo_type_name(accumulator)}",
                    location,
                    code="E2834",
                )
        return accumulator

    def _loop_bound(self, expression: Expression, env: Environment, location: SourceLocation) -> int:
        value = self.evaluate(expression, env)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EchoTypeError("for-loop bounds must be convertible to int", location, code="E2702")
        return int(value)

    def _try_match_switch_pattern(
        self,
        pattern: Pattern,
        value: object,
        env: Environment,
        location: SourceLocation,
    ) -> bool:
        if isinstance(pattern, LiteralPattern):
            return echo_equal(value, pattern.value)
        if isinstance(pattern, TypePattern):
            if not matches_type(value, pattern.type):
                return False
            if pattern.binding is not None:
                env.define(pattern.binding, value, pattern.type)
            return True
        return self._try_unpack_pattern(pattern, value, env, location)

    def _try_unpack_pattern(
        self,
        pattern: Pattern,
        value: object,
        env: Environment,
        location: SourceLocation,
    ) -> bool:
        if isinstance(pattern, ListPattern):
            if not isinstance(value, list):
                return False
            fixed = list_pattern_fixed(pattern)
            rest = list_pattern_rest(pattern)
            if rest is None:
                if len(value) != len(fixed):
                    return False
            elif len(value) < len(fixed):
                return False
            for index, element in enumerate(fixed):
                if not self._try_unpack_pattern(element, value[index], env, location):
                    return False
            if rest is not None:
                rest_value = list(value[len(fixed) :])
                if rest.declared_type is not None:
                    for item in rest_value:
                        if not matches_type(item, rest.declared_type):
                            return False
                self._bind_pattern_name(rest, rest_value, env, declare=True, const=False, location=location)
            return True
        if isinstance(pattern, HashPattern):
            if not isinstance(value, dict):
                return False
            for field in pattern.fields:
                source_key = field.source_key()
                if source_key not in value:
                    return False
                if field.declared_type is not None and not matches_type(value[source_key], field.declared_type):
                    return False
                self._bind_pattern_name(field, value[source_key], env, declare=True, const=False, location=location)
            return True
        if isinstance(pattern, NamePattern):
            if pattern.declared_type is not None and not matches_type(value, pattern.declared_type):
                return False
            self._bind_pattern_name(pattern, value, env, declare=True, const=False, location=location)
            return True
        return False

    def _unpack_pattern(
        self,
        pattern: Pattern,
        value: object,
        env: Environment,
        *,
        declare: bool,
        const: bool,
        location: SourceLocation,
    ) -> None:
        if isinstance(pattern, ListPattern):
            if not isinstance(value, list):
                raise EchoTypeError(
                    f"List destructuring expected a list, got {echo_type_name(value)}",
                    location,
                    code="E3206",
                )
            fixed = list_pattern_fixed(pattern)
            rest = list_pattern_rest(pattern)
            if rest is None:
                if len(value) != len(fixed):
                    raise EchoRuntimeError(
                        f"List destructuring expected {len(fixed)} element(s), got {len(value)}",
                        location,
                        code="E3205",
                    )
            elif len(value) < len(fixed):
                raise EchoRuntimeError(
                    f"List destructuring expected at least {len(fixed)} element(s), got {len(value)}",
                    location,
                    code="E3205",
                )
            for index, element in enumerate(fixed):
                self._unpack_pattern(
                    element,
                    value[index],
                    env,
                    declare=declare,
                    const=const,
                    location=location,
                )
            if rest is not None:
                rest_value = list(value[len(fixed) :])
                if rest.declared_type is not None:
                    for item in rest_value:
                        if not matches_type(item, rest.declared_type):
                            validate_type(rest.name, item, rest.declared_type, location)
                self._bind_pattern_name(rest, rest_value, env, declare=declare, const=const, location=location)
            return
        if isinstance(pattern, HashPattern):
            if not isinstance(value, dict):
                raise EchoTypeError(
                    f"Hash destructuring expected a hash, got {echo_type_name(value)}",
                    location,
                    code="E3207",
                )
            for field in pattern.fields:
                source_key = field.source_key()
                if source_key not in value:
                    raise EchoRuntimeError(f"Key '{source_key}' not found in hash", location, code="E2711")
                self._bind_pattern_name(
                    field, value[source_key], env, declare=declare, const=const, location=location
                )
            return
        if isinstance(pattern, NamePattern):
            self._bind_pattern_name(pattern, value, env, declare=declare, const=const, location=location)

    def _bind_pattern_name(
        self,
        pattern: NamePattern,
        value: object,
        env: Environment,
        *,
        declare: bool,
        const: bool,
        location: SourceLocation,
    ) -> None:
        declared_type = TypeName(pattern.location, "list") if pattern.rest else pattern.declared_type
        if declare:
            if declared_type is not None:
                validate_type(pattern.name, value, declared_type, location)
            if env.is_watched(pattern.name):
                self._watch(pattern.name, value, env)
            if const:
                freeze(value)
            env.define(pattern.name, value, declared_type, mutable=not const, const=const)
            return
        if env.is_watched(pattern.name):
            self._watch(pattern.name, value, env)
        env.assign(pattern.name, value, location)

    def _index_assign(self, target: object, index: object, value: object, location: SourceLocation) -> None:
        require_unfrozen(target, location)
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
