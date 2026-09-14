from __future__ import annotations

from collections.abc import Mapping

from echo.errors import ArgumentError, EchoTypeError, SemanticError, SourceLocation
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
    FunctionType,
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
    MemberExpression,
    NamePattern,
    ObjectType,
    Parameter,
    Pattern,
    Program,
    ReturnStatement,
    SliceExpression,
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
    iter_name_patterns,
    list_pattern_fixed,
    list_pattern_rest,
)
from echo.runtime.builtins import (
    MUTATING_METHODS,
    builtin_names,
    builtin_param_count,
    resolve_builtin_args,
    standalone_min_args,
)
from echo.runtime.functions import bind_arguments
from echo.runtime.values import format_type, function_signature_assignable, object_type_assignable
from echo.semantics.modules import ModuleSymbols
from echo.semantics.scope import Scope
from echo.semantics.symbols import Symbol, SymbolKind


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.module_symbols = ModuleSymbols()
        self._dependencies: Mapping[str, ModuleSymbols] = {}
        self._pending_exports: list[ExportDeclaration] = []
        self._return_types: list[TypeAnnotation | None] = []

    def analyze(
        self,
        program: Program,
        *,
        dependencies: Mapping[str, ModuleSymbols] | None = None,
        scope: Scope | None = None,
    ) -> Program:
        self.module_symbols = ModuleSymbols()
        self._dependencies = dependencies or {}
        self._pending_exports = []
        self._return_types = []
        if scope is None:
            scope = self.module_scope(program.location)
        self._statements(program.statements, scope)
        return program

    @staticmethod
    def module_scope(location: SourceLocation) -> Scope:
        scope = Scope()
        for name in builtin_names():
            scope.define(
                Symbol(
                    name=name,
                    kind=SymbolKind.FUNCTION,
                    location=location,
                    builtin=True,
                    param_count=builtin_param_count(name),
                )
            )
        return scope

    def collect_symbols(self, program: Program) -> ModuleSymbols:
        return self._collect_symbols(program)

    def analyze_modules(self, modules: Mapping[str, Program]) -> dict[str, ModuleSymbols]:
        catalog = {name: self._collect_symbols(program) for name, program in modules.items()}
        results: dict[str, ModuleSymbols] = {}
        for name, program in modules.items():
            analyzer = SemanticAnalyzer()
            analyzer.analyze(program, dependencies=catalog)
            results[name] = analyzer.module_symbols
        return results

    def _statements(self, statements: list[Statement], scope: Scope) -> None:
        for statement in statements:
            function = self._function_declaration(statement)
            if function is None:
                continue
            if isinstance(statement, ExportDeclaration):
                self._require_module_scope(scope, statement, "export")
            if function.return_type is not None:
                function.return_type = self._resolve_type(function.return_type, scope)
            symbol = self._function_symbol(function)
            scope.define(symbol)
            if scope.parent is None:
                self._record(symbol, exported=isinstance(statement, ExportDeclaration))
        for statement in statements:
            if isinstance(statement, ImportDeclaration):
                self._bind_import(statement, scope)
        for statement in statements:
            if isinstance(statement, ImportDeclaration):
                continue
            function = self._function_declaration(statement)
            if function is not None:
                if isinstance(statement, ExportDeclaration):
                    self._function_body(function, scope)
                else:
                    self._function_body(statement, scope)
            else:
                self._statement(statement, scope)
        if scope.parent is None:
            self._resolve_pending_exports()

    def _statement(self, statement: Statement, scope: Scope) -> None:
        if isinstance(statement, TypeAliasStatement):
            self._type_alias(statement, scope)
        elif isinstance(statement, VariableDeclaration):
            self._expression(statement.initializer, scope)
            statement.declared_type = self._resolve_type(statement.declared_type, scope)
            if isinstance(statement.declared_type, FunctionType):
                self._check_function_value_assignable(
                    statement.initializer,
                    statement.declared_type,
                    scope,
                    statement.location,
                    statement.name,
                )
            self._check_value_against_type(
                statement.initializer,
                statement.declared_type,
                scope,
                statement.location,
                statement.name,
            )
            symbol = Symbol(
                statement.name,
                SymbolKind.VARIABLE,
                statement.location,
                statement.declared_type,
                mutable=not statement.const,
                const=statement.const,
            )
            scope.define(symbol)
            if scope.parent is None:
                self._record(symbol)
        elif isinstance(statement, DestructureDeclaration):
            self._expression(statement.initializer, scope)
            self._resolve_pattern_types(statement.pattern, scope)
            self._check_pattern_against_value(statement.pattern, statement.initializer, statement.location, scope)
            self._define_pattern(statement.pattern, scope, const=statement.const, location=statement.location)
        elif isinstance(statement, DestructureAssignment):
            self._expression(statement.value, scope)
            self._assign_pattern(statement.pattern, scope, statement)
            self._check_pattern_against_value(statement.pattern, statement.value, statement.location, scope)
        elif isinstance(statement, AssignmentStatement):
            self._expression(statement.value, scope)
            self._require_assignable(statement.name, statement, scope)
            target = scope.resolve(statement.name)
            if target is not None and isinstance(target.declared_type, FunctionType):
                self._check_function_value_assignable(
                    statement.value,
                    target.declared_type,
                    scope,
                    statement.location,
                    statement.name,
                )
            if target is not None:
                self._check_value_against_type(
                    statement.value,
                    target.declared_type,
                    scope,
                    statement.location,
                    statement.name,
                )
        elif isinstance(statement, CompoundAssignment):
            self._expression(statement.value, scope)
            self._require_assignable(statement.name, statement, scope)
        elif isinstance(statement, IndexAssignment):
            self._require_variable(statement.name, statement, scope)
            self._require_not_const_mutation(statement.name, statement, scope)
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
            if isinstance(statement.iterable, ListLiteral):
                for item in statement.iterable.elements:
                    self._check_value_against_type(
                        item,
                        statement.var_type,
                        scope,
                        statement.location,
                        statement.var,
                    )
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
                if self._return_types:
                    self._check_value_against_type(
                        statement.value,
                        self._return_types[-1],
                        scope,
                        statement.location,
                        "return value",
                    )
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
                symbol = scope.resolve(name)
                if symbol is None:
                    raise SemanticError(f"Cannot import undefined variable '{name}'", statement.location, code="E1006")
                if statement.mutable and not symbol.mutable:
                    if symbol.const:
                        raise SemanticError(
                            f"Cannot use mut on const binding '{name}'",
                            statement.location,
                            help_text=f"'{name}' is declared with const.",
                            code="E3204",
                        )
                    raise SemanticError(
                        f"Cannot use mut on '{name}' because it is not a mutable binding",
                        statement.location,
                        code="E3107",
                    )
        elif isinstance(statement, ExportDeclaration):
            self._export_statement(statement, scope)
        elif isinstance(statement, ImportDeclaration):
            self._bind_import(statement, scope)
        elif isinstance(statement, WatchStatement):
            for name in statement.names:
                if scope.resolve(name) is None:
                    raise SemanticError(f"Cannot watch undefined variable '{name}'", statement.location, code="E1007")

    def _function_body(self, statement: FunctionDeclaration, scope: Scope) -> None:
        self._analyze_callable(
            statement.parameters,
            statement.body,
            statement.inline,
            statement.return_type,
            statement.location,
            statement.name,
            scope,
        )
        symbol = scope.resolve(statement.name)
        if symbol is not None and symbol.kind == SymbolKind.FUNCTION:
            symbol.param_types = [parameter.type for parameter in statement.parameters]
            symbol.param_defaults = [parameter.default is not None for parameter in statement.parameters]
            symbol.declared_type = statement.return_type

    def _analyze_callable(
        self,
        parameters: list[Parameter],
        body: list[Statement] | Expression,
        inline: bool,
        return_type: TypeAnnotation | None,
        location: SourceLocation,
        name: str,
        scope: Scope,
    ) -> None:
        for parameter in parameters:
            parameter.type = self._resolve_type(parameter.type, scope)

        has_return = self._contains_return(body)
        if has_return and return_type is None:
            kind = "lambda" if name == "<lambda>" else f"function '{name}'"
            raise SemanticError(
                f"Return type annotation required for {kind} because it contains a return statement",
                location,
                code="E1009",
            )

        function_scope = Scope(scope, is_function=True)
        for parameter in parameters:
            if parameter.default is not None:
                self._expression(parameter.default, function_scope)
            if parameter.pattern is not None:
                self._resolve_pattern_types(parameter.pattern, scope)
                self._define_pattern(parameter.pattern, function_scope, const=False, location=parameter.location)
            else:
                function_scope.define(Symbol(parameter.name, SymbolKind.VARIABLE, parameter.location, parameter.type))

        self._return_types.append(return_type)
        try:
            if inline:
                assert isinstance(body, Expression)
                self._expression(body, function_scope)
                self._check_value_against_type(body, return_type, function_scope, location, "return value")
            else:
                assert isinstance(body, list)
                self._statements(body, function_scope)
        finally:
            self._return_types.pop()

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
                if symbol.kind == SymbolKind.FUNCTION:
                    self._check_call_arity(symbol, expression, scope)
                elif symbol.kind == SymbolKind.VARIABLE:
                    declared = symbol.declared_type
                    if isinstance(declared, FunctionType):
                        self._check_function_type_arity(declared, expression)
                    elif not (isinstance(declared, TypeName) and declared.name == "dynamic"):
                        raise SemanticError(
                            f"Cannot call '{expression.callee.name}' because it is not a function",
                            expression.location,
                            code="E1014",
                        )
                else:
                    raise SemanticError(
                        f"Cannot call '{expression.callee.name}' because it is not a function",
                        expression.location,
                        code="E1014",
                    )
            elif isinstance(expression.callee, MemberExpression):
                self._expression(expression.callee.object, scope)
            else:
                self._expression(expression.callee, scope)
            self._check_const_mutation_call(expression, scope)
            for argument in expression.arguments:
                self._expression(argument.value, scope)
        elif isinstance(expression, MemberExpression):
            self._expression(expression.object, scope)
        elif isinstance(expression, IndexExpression):
            self._expression(expression.target, scope)
            self._expression(expression.index, scope)
        elif isinstance(expression, SliceExpression):
            self._expression(expression.target, scope)
            if expression.start is not None:
                self._expression(expression.start, scope)
            if expression.end is not None:
                self._expression(expression.end, scope)
        elif isinstance(expression, LambdaExpression):
            return_type = expression.return_type
            if return_type is not None:
                expression.return_type = self._resolve_type(return_type, scope)
            self._analyze_callable(
                expression.parameters,
                expression.body,
                expression.inline,
                expression.return_type,
                expression.location,
                "<lambda>",
                scope,
            )
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

    def _check_call_arity(self, symbol: Symbol, expression: CallExpression, scope: Scope) -> None:
        if symbol.builtin:
            self._check_builtin_call(symbol, expression)
            return
        if symbol.param_names is None:
            return
        parameters = self._parameters_from_symbol(symbol)
        try:
            bound = bind_arguments(symbol.name, parameters, expression.arguments, expression.location)
        except ArgumentError as exc:
            raise SemanticError(exc.message, expression.location, help_text=exc.help_text, code=exc.code) from exc
        types = symbol.param_types or []
        for index, name in enumerate(symbol.param_names):
            if index >= len(types):
                break
            expected = types[index]
            if name not in bound:
                continue
            if isinstance(expected, FunctionType):
                self._check_function_value_assignable(
                    bound[name],
                    expected,
                    scope,
                    expression.location,
                    name,
                )
            self._check_value_against_type(
                bound[name],
                expected,
                scope,
                expression.location,
                name,
            )

    def _check_function_type_arity(self, function_type: FunctionType, expression: CallExpression) -> None:
        if any(argument.name for argument in expression.arguments):
            return
        count = len(expression.arguments)
        expected = len(function_type.param_types)
        if function_type.variadic:
            minimum = max(0, expected - 1)
            if count < minimum:
                raise SemanticError(
                    f"Function value expected at least {minimum} argument(s), got {count}",
                    expression.location,
                    code="E2205",
                )
            return
        if count != expected:
            noun = "argument" if expected == 1 else "arguments"
            if count > expected:
                raise SemanticError(
                    f"Function value expected at most {expected} {noun}, got {count}",
                    expression.location,
                    code="E2202",
                )
            raise SemanticError(
                f"Function value expected {expected} {noun}, got {count}",
                expression.location,
                code="E2205",
            )

    def _check_function_value_assignable(
        self,
        expression: Expression,
        expected: FunctionType,
        scope: Scope,
        location: SourceLocation,
        name: str,
    ) -> None:
        signature = self._function_signature_of(expression, scope)
        if signature is None:
            return
        param_types, param_defaults, variadic, return_type = signature
        if function_signature_assignable(param_types, param_defaults, variadic, return_type, expected):
            return
        raise SemanticError(
            f"Cannot assign fn to {format_type(expected)} variable '{name}'",
            location,
            code="E2001",
        )

    def _function_signature_of(
        self,
        expression: Expression,
        scope: Scope,
    ) -> tuple[list[TypeAnnotation], list[bool], bool, TypeAnnotation | None] | None:
        if isinstance(expression, LambdaExpression):
            return (
                [parameter.type for parameter in expression.parameters],
                [parameter.default is not None for parameter in expression.parameters],
                any(parameter.variadic for parameter in expression.parameters),
                expression.return_type,
            )
        if isinstance(expression, VariableExpression):
            symbol = scope.resolve(expression.name)
            if symbol is None or symbol.kind != SymbolKind.FUNCTION or symbol.builtin:
                return None
            return (
                symbol.param_types or [],
                symbol.param_defaults or [False] * len(symbol.param_names or []),
                symbol.variadic,
                symbol.declared_type,
            )
        return None

    def _parameters_from_symbol(self, symbol: Symbol) -> list[Parameter]:
        names = symbol.param_names or []
        defaults = symbol.param_defaults or [False] * len(names)
        dummy_type = TypeName(symbol.location, "dynamic")
        dummy_default = LiteralExpression(symbol.location, None)
        parameters: list[Parameter] = []
        for index, name in enumerate(names):
            variadic = bool(symbol.variadic) and index == len(names) - 1
            has_default = defaults[index] if index < len(defaults) else False
            default = dummy_default if has_default and not variadic else None
            parameters.append(Parameter(name, dummy_type, symbol.location, default, variadic))
        return parameters

    def _check_builtin_call(self, symbol: Symbol, expression: CallExpression) -> None:
        try:
            resolve_builtin_args(symbol.name, expression.arguments, False, expression.location)
        except (ArgumentError, EchoTypeError) as exc:
            raise SemanticError(exc.message, expression.location, help_text=exc.help_text, code=exc.code) from exc
        if any(argument.name for argument in expression.arguments):
            return
        required = standalone_min_args(symbol.name)
        if required is None:
            return
        count = len(expression.arguments)
        if required == 0 and count > 0:
            raise SemanticError(f"{symbol.name}() takes no arguments", expression.location, code="E2807")
        if count < required:
            if symbol.name == "wait":
                message = "wait() requires a seconds argument"
                code = "E2608"
            elif symbol.name == "format":
                message = "format() requires a template string"
                code = "E2615"
            else:
                message = f"{symbol.name}() expected at least {required} argument(s)"
                code = "E2620"
            raise SemanticError(message, expression.location, code=code)

    def _collect_symbols(self, program: Program) -> ModuleSymbols:
        symbols = ModuleSymbols()
        declared: dict[str, Symbol] = {}
        pending: list[ExportDeclaration] = []

        def add(symbol: Symbol, exported: bool) -> None:
            if symbol.name in declared:
                existing = declared[symbol.name]
                kind = "function" if existing.kind == SymbolKind.FUNCTION else "name"
                raise SemanticError(
                    f"{kind.capitalize()} '{symbol.name}' is already declared",
                    symbol.location,
                    code="E1001",
                )
            declared[symbol.name] = symbol
            if exported:
                symbols.exports[symbol.name] = symbol
            else:
                symbols.private[symbol.name] = symbol

        for statement in program.statements:
            if isinstance(statement, ExportDeclaration):
                if isinstance(statement.declaration, FunctionDeclaration):
                    add(self._function_symbol(statement.declaration), True)
                elif isinstance(statement.declaration, VariableDeclaration):
                    add(self._variable_symbol(statement.declaration), True)
                else:
                    pending.append(statement)
            elif isinstance(statement, FunctionDeclaration):
                add(self._function_symbol(statement), False)
            elif isinstance(statement, VariableDeclaration):
                add(self._variable_symbol(statement), False)
            elif isinstance(statement, DestructureDeclaration):
                for name_pattern in iter_name_patterns(statement.pattern):
                    declared = TypeName(name_pattern.location, "list") if name_pattern.rest else name_pattern.declared_type
                    add(
                        Symbol(
                            name_pattern.name,
                            SymbolKind.VARIABLE,
                            name_pattern.location,
                            declared,
                            mutable=not statement.const,
                            const=statement.const,
                        ),
                        False,
                    )

        for statement in pending:
            existing = declared.get(statement.name)
            if existing is None:
                raise SemanticError(
                    f"Cannot export '{statement.name}' because it is not declared",
                    statement.location,
                    code="E3101",
                )
            if statement.name in symbols.private:
                symbols.exports[statement.name] = symbols.private.pop(statement.name)
        return symbols

    def _function_declaration(self, statement: Statement) -> FunctionDeclaration | None:
        if isinstance(statement, FunctionDeclaration):
            return statement
        if isinstance(statement, ExportDeclaration) and isinstance(statement.declaration, FunctionDeclaration):
            return statement.declaration
        return None

    def _function_symbol(self, statement: FunctionDeclaration) -> Symbol:
        return Symbol(
            statement.name,
            SymbolKind.FUNCTION,
            statement.location,
            statement.return_type,
            param_count=len(statement.parameters),
            param_names=[parameter.name for parameter in statement.parameters],
            param_types=[parameter.type for parameter in statement.parameters],
            param_defaults=[parameter.default is not None for parameter in statement.parameters],
            variadic=any(parameter.variadic for parameter in statement.parameters),
        )

    def _variable_symbol(self, statement: VariableDeclaration) -> Symbol:
        return Symbol(
            statement.name,
            SymbolKind.VARIABLE,
            statement.location,
            statement.declared_type,
            mutable=not statement.const,
            const=statement.const,
        )

    def _imported_symbol(self, exported: Symbol, statement: ImportDeclaration) -> Symbol:
        return Symbol(
            exported.name,
            exported.kind,
            statement.location,
            exported.declared_type,
            mutable=False,
            param_count=exported.param_count,
            param_names=exported.param_names,
            param_types=exported.param_types,
            param_defaults=exported.param_defaults,
            variadic=exported.variadic,
            imported=True,
            const=exported.const,
        )

    def _record(self, symbol: Symbol, *, exported: bool = False) -> None:
        if symbol.imported:
            self.module_symbols.imports[symbol.name] = symbol
        elif exported:
            self.module_symbols.exports[symbol.name] = symbol
        else:
            self.module_symbols.private[symbol.name] = symbol

    def _require_module_scope(self, scope: Scope, statement: Statement, construct: str) -> None:
        if scope.parent is not None:
            raise SemanticError(
                f"'{construct}' can only appear at module scope",
                statement.location,
                code="E3100",
            )

    def _bind_import(self, statement: ImportDeclaration, scope: Scope) -> None:
        self._require_module_scope(scope, statement, "import")
        dependency = self._dependencies.get(statement.module)
        if dependency is None:
            raise SemanticError(
                f"Cannot import '{statement.name}' from '{statement.module}'",
                statement.location,
                code="E3104",
            )
        exported = dependency.exports.get(statement.name)
        if exported is None:
            if statement.name in dependency.private:
                raise SemanticError(
                    f"Cannot import '{statement.name}' from '{statement.module}' because it is not exported",
                    statement.location,
                    code="E3102",
                )
            raise SemanticError(
                f"Cannot import '{statement.name}' from '{statement.module}' because it does not exist",
                statement.location,
                code="E3103",
            )
        bound = self._imported_symbol(exported, statement)
        scope.define(bound)
        self._record(bound)

    def _export_statement(self, statement: ExportDeclaration, scope: Scope) -> None:
        self._require_module_scope(scope, statement, "export")
        if isinstance(statement.declaration, VariableDeclaration):
            self._statement(statement.declaration, scope)
            self._mark_exported(statement.name, statement)
            return
        self._pending_exports.append(statement)

    def _resolve_pending_exports(self) -> None:
        for statement in self._pending_exports:
            self._mark_exported(statement.name, statement)
        self._pending_exports = []

    def _mark_exported(self, name: str, statement: ExportDeclaration) -> None:
        if name in self.module_symbols.exports:
            return
        if name in self.module_symbols.imports:
            raise SemanticError(
                f"Cannot re-export imported name '{name}'",
                statement.location,
                code="E3101",
            )
        symbol = self.module_symbols.private.pop(name, None)
        if symbol is None:
            raise SemanticError(
                f"Cannot export '{name}' because it is not declared",
                statement.location,
                code="E3101",
            )
        self.module_symbols.exports[name] = symbol

    def _resolve_pattern_types(self, pattern: Pattern, scope: Scope) -> None:
        if isinstance(pattern, NamePattern):
            if pattern.declared_type is not None:
                pattern.declared_type = self._resolve_type(pattern.declared_type, scope)
            return
        if isinstance(pattern, ListPattern):
            for element in pattern.elements:
                self._resolve_pattern_types(element, scope)
            return
        if isinstance(pattern, HashPattern):
            for field in pattern.fields:
                self._resolve_pattern_types(field, scope)

    def _binding_type(self, pattern: NamePattern) -> TypeAnnotation:
        if pattern.rest:
            return TypeName(pattern.location, "list")
        assert pattern.declared_type is not None
        return pattern.declared_type

    def _define_pattern(self, pattern: Pattern, scope: Scope, *, const: bool, location: SourceLocation) -> None:
        for name_pattern in iter_name_patterns(pattern):
            declared = self._binding_type(name_pattern)
            symbol = Symbol(
                name_pattern.name,
                SymbolKind.VARIABLE,
                name_pattern.location,
                declared,
                mutable=not const,
                const=const,
            )
            scope.define(symbol)
            if scope.parent is None:
                self._record(symbol)

    def _assign_pattern(self, pattern: Pattern, scope: Scope, statement: Statement) -> None:
        for name_pattern in iter_name_patterns(pattern):
            self._require_assignable(name_pattern.name, statement, scope)

    def _check_pattern_against_value(
        self,
        pattern: Pattern,
        value: Expression,
        location: SourceLocation,
        scope: Scope,
    ) -> None:
        if isinstance(pattern, ListPattern):
            if isinstance(value, HashLiteral) or isinstance(value, StringLiteralExpression):
                raise SemanticError(
                    "List destructuring expected a list",
                    location,
                    code="E3206",
                )
            if isinstance(value, LiteralExpression) and not isinstance(value.value, list):
                raise SemanticError(
                    "List destructuring expected a list",
                    location,
                    code="E3206",
                )
            if not isinstance(value, ListLiteral):
                return
            fixed = list_pattern_fixed(pattern)
            rest = list_pattern_rest(pattern)
            actual = len(value.elements)
            if rest is None:
                if actual != len(fixed):
                    raise SemanticError(
                        f"List destructuring expected {len(fixed)} element(s), got {actual}",
                        location,
                        code="E3205",
                    )
            elif actual < len(fixed):
                raise SemanticError(
                    f"List destructuring expected at least {len(fixed)} element(s), got {actual}",
                    location,
                    code="E3205",
                )
            for element_pattern, element_value in zip(fixed, value.elements):
                self._check_pattern_against_value(element_pattern, element_value, location, scope)
            return
        if isinstance(pattern, HashPattern):
            if isinstance(value, ListLiteral) or isinstance(value, StringLiteralExpression):
                raise SemanticError(
                    "Hash destructuring expected a hash",
                    location,
                    code="E3207",
                )
            if isinstance(value, LiteralExpression) and not isinstance(value.value, dict):
                raise SemanticError(
                    "Hash destructuring expected a hash",
                    location,
                    code="E3207",
                )
            if not isinstance(value, HashLiteral):
                source = scope.resolve(value.name) if isinstance(value, VariableExpression) else None
                source_type = source.declared_type if source is not None else None
                if isinstance(source_type, ObjectType):
                    for field in pattern.fields:
                        expected = field.declared_type
                        actual = source_type.fields.get(field.name)
                        if (
                            isinstance(expected, ObjectType)
                            and isinstance(actual, ObjectType)
                            and not object_type_assignable(actual, expected)
                        ):
                            raise SemanticError(
                                f"Cannot assign {format_type(actual)} to {format_type(expected)} "
                                f"variable '{field.name}'",
                                location,
                                help_text="An open hash type is not assignable to an exact type "
                                "(it might have extra fields).",
                                code="E2001",
                            )
                return
            keys = {pair.key for pair in value.pairs}
            pairs = {pair.key: pair.value for pair in value.pairs}
            for field in pattern.fields:
                if field.name not in keys:
                    raise SemanticError(
                        f"Key '{field.name}' not found in hash",
                        location,
                        code="E2711",
                    )
                self._check_pattern_field_type(field, pairs[field.name], location, scope)
            return
        if isinstance(pattern, NamePattern):
            self._check_pattern_field_type(pattern, value, location, scope)

    def _check_pattern_field_type(
        self,
        field: NamePattern,
        value: Expression,
        location: SourceLocation,
        scope: Scope,
    ) -> None:
        expected = field.declared_type
        if expected is None:
            symbol = scope.resolve(field.name)
            expected = symbol.declared_type if symbol is not None else None
        if expected is None:
            return
        self._check_value_against_type(value, expected, scope, location, field.name)

    def _check_value_against_type(
        self,
        expression: Expression,
        expected: TypeAnnotation | None,
        scope: Scope,
        location: SourceLocation,
        name: str,
    ) -> None:
        if not isinstance(expected, ObjectType):
            return
        if isinstance(expression, HashLiteral):
            self._check_hash_literal_against_object(expression, expected, scope, location, name)
            return
        if isinstance(expression, VariableExpression):
            symbol = scope.resolve(expression.name)
            if symbol is None or not isinstance(symbol.declared_type, ObjectType):
                return
            if object_type_assignable(symbol.declared_type, expected):
                return
            raise SemanticError(
                f"Cannot assign {format_type(symbol.declared_type)} to {format_type(expected)} variable '{name}'",
                location,
                help_text="An open hash type is not assignable to an exact type (it might have extra fields).",
                code="E2001",
            )

    def _check_hash_literal_against_object(
        self,
        expression: HashLiteral,
        expected: ObjectType,
        scope: Scope,
        location: SourceLocation,
        name: str,
    ) -> None:
        keys = {pair.key for pair in expression.pairs}
        if expected.exact:
            for field_name in expected.fields:
                if field_name not in keys:
                    raise SemanticError(
                        f"Exact type {format_type(expected)} is missing required field '{field_name}'",
                        location,
                        help_text="Exact types require every listed field.",
                        code="E3209",
                    )
            for pair in expression.pairs:
                if pair.key not in expected.fields:
                    raise SemanticError(
                        f"Exact type {format_type(expected)} does not allow extra field '{pair.key}'",
                        location,
                        help_text="Remove extra fields, or use an open hash type { ... } if extras are allowed.",
                        code="E3208",
                    )
        for pair in expression.pairs:
            field_type = expected.fields.get(pair.key)
            if isinstance(field_type, ObjectType):
                self._check_value_against_type(pair.value, field_type, scope, location, f"{name}.{pair.key}")

    def _require_assignable(self, name: str, statement: Statement, scope: Scope) -> None:
        symbol = scope.resolve(name)
        if symbol is not None and symbol.const:
            raise SemanticError(
                f"Cannot reassign const binding '{name}'",
                statement.location,
                help_text=f"'{name}' is declared with const.",
                code="E3201",
            )
        if symbol is not None and not symbol.mutable:
            raise SemanticError(
                f"Cannot rebind imported name '{name}'",
                statement.location,
                code="E3106",
            )
        self._require_variable(name, statement, scope)

    def _require_not_const_mutation(self, name: str, node: Statement | Expression, scope: Scope) -> None:
        symbol = scope.resolve(name)
        if symbol is not None and symbol.const:
            raise SemanticError(
                f"Cannot mutate const binding '{name}'",
                node.location,
                help_text=f"'{name}' is declared with const and cannot be changed in place.",
                code="E3202",
            )

    def _check_const_mutation_call(self, expression: CallExpression, scope: Scope) -> None:
        callee = expression.callee
        method: str | None = None
        target_name: str | None = None
        if isinstance(callee, MemberExpression) and callee.name in MUTATING_METHODS:
            method = callee.name
            if isinstance(callee.object, VariableExpression):
                target_name = callee.object.name
        elif isinstance(callee, VariableExpression) and callee.name in MUTATING_METHODS:
            method = callee.name
            if expression.arguments:
                argument = expression.arguments[0]
                if argument.name is None and isinstance(argument.value, VariableExpression):
                    target_name = argument.value.name
        if method is None or target_name is None:
            return
        symbol = scope.resolve(target_name)
        if symbol is not None and method == "reverse" and isinstance(symbol.declared_type, TypeName) and symbol.declared_type.name == "str":
            return
        self._require_not_const_mutation(target_name, expression, scope)

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
        if isinstance(type_annotation, FunctionType):
            param_types = [self._resolve_type(param_type, scope) for param_type in type_annotation.param_types]
            return_type = self._resolve_type(type_annotation.return_type, scope)
            return FunctionType(type_annotation.location, param_types, return_type, type_annotation.variadic)
        if isinstance(type_annotation, ObjectType):
            fields = {
                name: self._resolve_type(field_type, scope)
                for name, field_type in type_annotation.fields.items()
            }
            return ObjectType(type_annotation.location, fields, type_annotation.exact)
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
