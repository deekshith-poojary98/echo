from __future__ import annotations

from echo.errors import ArgumentError, EchoTypeError, SemanticError
from echo.frontend.ast.nodes import (
    AssignmentStatement,
    BinaryExpression,
    BreakStatement,
    CallExpression,
    CompoundAssignment,
    ContinueStatement,
    Expression,
    ExpressionStatement,
    ForStatement,
    ForeachStatement,
    FunctionDeclaration,
    HashLiteral,
    IfStatement,
    IndexAssignment,
    IndexExpression,
    ListLiteral,
    LiteralExpression,
    MemberExpression,
    ObjectType,
    Program,
    ReturnStatement,
    Statement,
    StringInterpolation,
    StringLiteralExpression,
    TypeAliasStatement,
    TypeAnnotation,
    TypeName,
    UnaryExpression,
    UseStatement,
    VariableDeclaration,
    VariableExpression,
    WatchStatement,
    WhileStatement,
)
from echo.runtime.builtins import builtin_names, builtin_param_count, resolve_builtin_args, standalone_min_args
from echo.runtime.functions import bind_arguments
from echo.semantics.scope import Scope
from echo.semantics.symbols import Symbol, SymbolKind


class SemanticAnalyzer:
    def analyze(self, program: Program) -> Program:
        scope = Scope()
        for name in builtin_names():
            scope.define(
                Symbol(
                    name=name,
                    kind=SymbolKind.FUNCTION,
                    location=program.location,
                    builtin=True,
                    param_count=builtin_param_count(name),
                )
            )
        self._statements(program.statements, scope)
        return program

    def _statements(self, statements: list[Statement], scope: Scope) -> None:
        for statement in statements:
            if isinstance(statement, FunctionDeclaration):
                if statement.return_type is not None:
                    statement.return_type = self._resolve_type(statement.return_type, scope)
                scope.define(
                    Symbol(
                        statement.name,
                        SymbolKind.FUNCTION,
                        statement.location,
                        statement.return_type,
                        param_count=len(statement.parameters),
                        param_names=[parameter.name for parameter in statement.parameters],
                    )
                )
        for statement in statements:
            if isinstance(statement, FunctionDeclaration):
                self._function_body(statement, scope)
            else:
                self._statement(statement, scope)

    def _statement(self, statement: Statement, scope: Scope) -> None:
        if isinstance(statement, TypeAliasStatement):
            self._type_alias(statement, scope)
        elif isinstance(statement, VariableDeclaration):
            self._expression(statement.initializer, scope)
            statement.declared_type = self._resolve_type(statement.declared_type, scope)
            scope.define(
                Symbol(statement.name, SymbolKind.VARIABLE, statement.location, statement.declared_type)
            )
        elif isinstance(statement, AssignmentStatement):
            self._expression(statement.value, scope)
            self._require_variable(statement.name, statement, scope)
        elif isinstance(statement, CompoundAssignment):
            self._expression(statement.value, scope)
            self._require_variable(statement.name, statement, scope)
        elif isinstance(statement, IndexAssignment):
            self._require_variable(statement.name, statement, scope)
            for index in statement.indices:
                self._expression(index, scope)
            self._expression(statement.value, scope)
        elif isinstance(statement, ExpressionStatement):
            self._expression(statement.expression, scope)
        elif isinstance(statement, IfStatement):
            self._expression(statement.condition, scope)
            self._statements(statement.then_branch, Scope(scope))
            if statement.else_branch:
                self._statements(statement.else_branch, Scope(scope))
        elif isinstance(statement, WhileStatement):
            self._expression(statement.condition, scope)
            self._statements(statement.body, Scope(scope, is_loop=True))
        elif isinstance(statement, ForStatement):
            statement.var_type = self._resolve_type(statement.var_type, scope)
            if isinstance(statement.var_type, TypeName) and statement.var_type.name != "int":
                raise SemanticError(
                    f"For loop variable must be of type int, got {statement.var_type.name}",
                    statement.location,
                    code="E1008",
                )
            self._expression(statement.start, scope)
            self._expression(statement.end, scope)
            self._expression(statement.step, scope)
            loop_scope = Scope(scope, is_loop=True)
            loop_scope.define(Symbol(statement.var, SymbolKind.VARIABLE, statement.location, statement.var_type))
            self._statements(statement.body, loop_scope)
        elif isinstance(statement, ForeachStatement):
            statement.var_type = self._resolve_type(statement.var_type, scope)
            self._expression(statement.iterable, scope)
            loop_scope = Scope(scope, is_loop=True)
            loop_scope.define(Symbol(statement.var, SymbolKind.VARIABLE, statement.location, statement.var_type))
            self._statements(statement.body, loop_scope)
        elif isinstance(statement, FunctionDeclaration):
            self._function_body(statement, scope)
        elif isinstance(statement, ReturnStatement):
            if not scope.in_function:
                raise SemanticError(
                    "'return' statement outside function",
                    statement.location,
                    help_text="'return' can only be used inside a function body.",
                    code="E1003",
                )
            if statement.value is not None:
                self._expression(statement.value, scope)
        elif isinstance(statement, BreakStatement):
            if not scope.is_loop:
                raise SemanticError(
                    "'break' statement outside loop",
                    statement.location,
                    help_text="'break' can only be used inside for/foreach/while loops.",
                    code="E1004",
                )
        elif isinstance(statement, ContinueStatement):
            if not scope.is_loop:
                raise SemanticError(
                    "'continue' statement outside loop",
                    statement.location,
                    help_text="'continue' can only be used inside for/foreach/while loops.",
                    code="E1004",
                )
        elif isinstance(statement, UseStatement):
            if not scope.in_function:
                raise SemanticError("'use' statements can only be used inside functions", statement.location, code="E1005")
            for name in statement.names:
                if scope.resolve(name) is None:
                    raise SemanticError(f"Cannot import undefined variable '{name}'", statement.location, code="E1006")
        elif isinstance(statement, WatchStatement):
            for name in statement.names:
                if scope.resolve(name) is None:
                    raise SemanticError(f"Cannot watch undefined variable '{name}'", statement.location, code="E1007")

    def _function_body(self, statement: FunctionDeclaration, scope: Scope) -> None:
        for parameter in statement.parameters:
            parameter.type = self._resolve_type(parameter.type, scope)

        has_return = self._contains_return(statement.body)
        if has_return and statement.return_type is None:
            raise SemanticError(
                f"Return type annotation required for function '{statement.name}' because it contains a return statement",
                statement.location,
                code="E1009",
            )

        function_scope = Scope(scope, is_function=True)
        for parameter in statement.parameters:
            function_scope.define(Symbol(parameter.name, SymbolKind.VARIABLE, parameter.location, parameter.type))

        if statement.inline:
            assert isinstance(statement.body, Expression)
            self._expression(statement.body, function_scope)
        else:
            assert isinstance(statement.body, list)
            self._statements(statement.body, function_scope)

    def _expression(self, expression: Expression, scope: Scope) -> None:
        if isinstance(expression, VariableExpression):
            if scope.resolve(expression.name) is None:
                raise SemanticError(
                    f"Variable '{expression.name}' is not defined",
                    expression.location,
                    help_text="Declare the variable with a type before using it.",
                    code="E1002",
                )
        elif isinstance(expression, BinaryExpression):
            self._expression(expression.left, scope)
            self._expression(expression.right, scope)
        elif isinstance(expression, UnaryExpression):
            self._expression(expression.operand, scope)
        elif isinstance(expression, CallExpression):
            if isinstance(expression.callee, VariableExpression):
                symbol = scope.resolve(expression.callee.name)
                if symbol is None:
                    raise SemanticError(
                        f"Function '{expression.callee.name}' is not defined",
                        expression.location,
                        help_text="Define the function with 'fn name(...) { ... }' before calling it.",
                        code="E1010",
                    )
                if symbol.kind != SymbolKind.FUNCTION:
                    raise SemanticError(
                        f"Cannot call '{expression.callee.name}' because it is not a function",
                        expression.location,
                        code="E1014",
                    )
                self._check_call_arity(symbol, expression)
            elif isinstance(expression.callee, MemberExpression):
                self._expression(expression.callee.object, scope)
            else:
                self._expression(expression.callee, scope)
            for argument in expression.arguments:
                self._expression(argument.value, scope)
        elif isinstance(expression, MemberExpression):
            self._expression(expression.object, scope)
        elif isinstance(expression, IndexExpression):
            self._expression(expression.target, scope)
            self._expression(expression.index, scope)
        elif isinstance(expression, ListLiteral):
            for element in expression.elements:
                self._expression(element, scope)
        elif isinstance(expression, HashLiteral):
            for pair in expression.pairs:
                self._expression(pair.value, scope)
        elif isinstance(expression, StringInterpolation):
            for part in expression.parts:
                self._expression(part, scope)
        elif isinstance(expression, (LiteralExpression, StringLiteralExpression)):
            return

    def _check_call_arity(self, symbol: Symbol, expression: CallExpression) -> None:
        if symbol.builtin:
            self._check_builtin_call(symbol, expression)
            return
        if symbol.param_names is None:
            return
        try:
            bind_arguments(symbol.name, symbol.param_names, expression.arguments, expression.location)
        except ArgumentError as exc:
            raise SemanticError(exc.message, expression.location, help_text=exc.help_text, code=exc.code) from exc

    def _check_builtin_call(self, symbol: Symbol, expression: CallExpression) -> None:
        try:
            resolve_builtin_args(symbol.name, expression.arguments, False, expression.location)
        except (ArgumentError, EchoTypeError) as exc:
            raise SemanticError(exc.message, expression.location, help_text=exc.help_text, code=exc.code) from exc
        if any(argument.name for argument in expression.arguments):
            return
        required = standalone_min_args(symbol.name)
        if required is not None and len(expression.arguments) < required:
            if symbol.name == "wait":
                message = "wait() requires a seconds argument"
                code = "E2608"
            elif symbol.name == "format":
                message = "format() requires a template string"
                code = "E2615"
            else:
                message = f"{symbol.name}() requires a target or at least one argument"
                code = "E2620"
            raise SemanticError(message, expression.location, code=code)

    def _require_variable(self, name: str, statement: Statement, scope: Scope) -> None:
        symbol = scope.resolve(name)
        if symbol is None or symbol.kind != SymbolKind.VARIABLE:
            raise SemanticError(
                f"Variable '{name}' is not declared",
                statement.location,
                help_text='Declare variables with a type before assigning, e.g. name: str = "Echo";',
                code="E1011",
            )

    def _type_alias(self, statement: TypeAliasStatement, scope: Scope) -> None:
        if statement.name in scope.type_aliases:
            raise SemanticError(f"Type alias '{statement.name}' is already defined", statement.location, code="E1012")
        resolved = self._resolve_type(statement.target, scope)
        scope.type_aliases[statement.name] = resolved
        statement.target = resolved

    def _resolve_type(self, type_annotation: TypeAnnotation, scope: Scope) -> TypeAnnotation:
        if isinstance(type_annotation, ObjectType):
            fields = {
                name: self._resolve_type(field_type, scope)
                for name, field_type in type_annotation.fields.items()
            }
            return ObjectType(type_annotation.location, fields)
        if isinstance(type_annotation, TypeName):
            if type_annotation.name in {"int", "float", "str", "bool", "dynamic", "list", "hash", "void"}:
                return type_annotation
            alias = scope.type_aliases.get(type_annotation.name)
            if alias is None:
                raise SemanticError(
                    f"Unknown type alias '{type_annotation.name}'",
                    type_annotation.location,
                    code="E1013",
                )
            return alias
        return type_annotation

    def _contains_return(self, body: list[Statement] | Expression) -> bool:
        if not isinstance(body, list):
            return False
        for statement in body:
            if isinstance(statement, ReturnStatement):
                return True
            if isinstance(statement, FunctionDeclaration):
                continue
            for key in ("then_branch", "else_branch", "body"):
                branch = getattr(statement, key, None)
                if isinstance(branch, list) and self._contains_return(branch):
                    return True
        return False
