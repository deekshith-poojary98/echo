from __future__ import annotations

from dataclasses import dataclass, field

from echo.errors import SourceLocation
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
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.frontend.tokens import TokenType
from echo.runtime.builtins import builtin_names
from echo.runtime.testing import is_test_entry


RULES = {
    "unused-local": "declared local, parameter, or loop variable is never read",
    "unused-function": "function is never called in this file, is not exported, and is not a zero-arg test* entry",
    "unused-import": "imported name is never used",
    "comparison-to-bool": "== true / != false and the other boolean-literal comparisons",
    "redundant-by-one": "explicit `by 1` on for; the formatter omits it",
    "empty-block": "empty if/else body or empty function body",
    "shadow-builtin": "a declared name shadows a builtin",
    "test-naming": "top-level fn looks like a test but is not a zero-arg testXxx entry",
    "self-assign": "assignment of a name to itself, or to itself plus zero",
    "unreachable-after-fail": "statement in the same block after fail(...) or return",
}


@dataclass(frozen=True)
class LintFinding:
    path: str
    line: int
    column: int
    rule: str
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}:{self.column}: {self.rule}: {self.message}"


def lint_source(source: str, filename: str = "<input>") -> list[LintFinding]:
    tokens = Lexer().tokenize(source, filename=filename)
    program = Parser(tokens).parse()
    return lint_program(program, filename)


def lint_program(program: Program, filename: str = "<input>") -> list[LintFinding]:
    linter = _Linter(filename)
    linter.lint_program(program)
    return linter.findings()


def format_finding(finding: LintFinding) -> str:
    return finding.format()


@dataclass
class _Binding:
    name: str
    kind: str
    location: SourceLocation
    used: bool = False


@dataclass
class _Scope:
    parent: _Scope | None = None
    bindings: dict[str, _Binding] = field(default_factory=dict)

    def define(self, binding: _Binding) -> None:
        self.bindings[binding.name] = binding

    def resolve(self, name: str) -> _Binding | None:
        current: _Scope | None = self
        while current is not None:
            binding = current.bindings.get(name)
            if binding is not None:
                return binding
            current = current.parent
        return None

    def mark_used(self, name: str) -> None:
        binding = self.resolve(name)
        if binding is not None:
            binding.used = True


class _Linter:
    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._findings: list[LintFinding] = []
        self._builtins = builtin_names()

    def findings(self) -> list[LintFinding]:
        return sorted(self._findings, key=lambda item: (item.line, item.column, item.rule, item.message))

    def lint_program(self, program: Program) -> None:
        for statement in program.statements:
            function = self._function_of(statement)
            if function is not None:
                self._test_naming(function)
        scope = _Scope()
        self._block(program.statements, scope, allow_test_entries=True)

    def _block(self, statements: list[Statement], scope: _Scope, *, allow_test_entries: bool = False) -> None:
        self._unreachable(statements)
        exported: set[str] = set()
        for statement in statements:
            function = self._function_of(statement)
            if function is not None:
                self._shadow(function.name, function.location)
                used = allow_test_entries and is_test_entry(function.name, len(function.parameters))
                scope.define(_Binding(function.name, "function", function.location, used=used))
            if isinstance(statement, ExportDeclaration):
                exported.add(statement.name)
        for statement in statements:
            if isinstance(statement, ImportDeclaration):
                self._import(statement, scope)
        for statement in statements:
            if isinstance(statement, ImportDeclaration):
                continue
            self._statement(statement, scope)
        self._report_unused(scope, exported)

    def _statement(self, statement: Statement, scope: _Scope) -> None:
        if isinstance(statement, VariableDeclaration):
            self._expr(statement.initializer, scope)
            self._shadow(statement.name, statement.location)
            scope.define(_Binding(statement.name, "local", statement.location))
            return
        if isinstance(statement, AssignmentStatement):
            self._self_assign(statement)
            self._expr(statement.value, scope)
            return
        if isinstance(statement, CompoundAssignment):
            scope.mark_used(statement.name)
            self._expr(statement.value, scope)
            return
        if isinstance(statement, IndexAssignment):
            scope.mark_used(statement.name)
            for index in statement.indices:
                self._expr(index, scope)
            self._expr(statement.value, scope)
            return
        if isinstance(statement, ExpressionStatement):
            self._expr(statement.expression, scope)
            return
        if isinstance(statement, IfStatement):
            self._if_statement(statement, scope)
            return
        if isinstance(statement, WhileStatement):
            self._expr(statement.condition, scope)
            self._block(statement.body, _Scope(scope))
            return
        if isinstance(statement, ForStatement):
            self._for_statement(statement, scope)
            return
        if isinstance(statement, ForeachStatement):
            self._expr(statement.iterable, scope)
            self._shadow(statement.var, statement.location)
            loop = _Scope(scope)
            loop.define(_Binding(statement.var, "local", statement.location))
            self._block(statement.body, loop)
            return
        if isinstance(statement, FunctionDeclaration):
            self._function_body(statement, scope)
            return
        if isinstance(statement, ReturnStatement):
            if statement.value is not None:
                self._expr(statement.value, scope)
            return
        if isinstance(statement, (BreakStatement, ContinueStatement, TypeAliasStatement)):
            return
        if isinstance(statement, UseStatement):
            for name in statement.names:
                scope.mark_used(name)
            return
        if isinstance(statement, WatchStatement):
            for name in statement.names:
                scope.mark_used(name)
            return
        if isinstance(statement, ExportDeclaration):
            if statement.declaration is not None:
                self._statement(statement.declaration, scope)
            return

    def _import(self, statement: ImportDeclaration, scope: _Scope) -> None:
        self._shadow(statement.name, statement.location)
        scope.define(_Binding(statement.name, "import", statement.location))

    def _if_statement(self, statement: IfStatement, scope: _Scope) -> None:
        self._expr(statement.condition, scope)
        if not statement.then_branch:
            self._finding(statement.location, "empty-block", "empty if body")
        else:
            self._block(statement.then_branch, _Scope(scope))
        if statement.else_branch is None:
            return
        if not statement.else_branch:
            self._finding(statement.location, "empty-block", "empty else body")
            return
        if len(statement.else_branch) == 1 and isinstance(statement.else_branch[0], IfStatement):
            self._if_statement(statement.else_branch[0], scope)
            return
        self._block(statement.else_branch, _Scope(scope))

    def _for_statement(self, statement: ForStatement, scope: _Scope) -> None:
        self._expr(statement.start, scope)
        self._expr(statement.end, scope)
        self._expr(statement.step, scope)
        if self._redundant_by_one(statement):
            self._finding(statement.step.location, "redundant-by-one", "redundant 'by 1'; the formatter omits it")
        self._shadow(statement.var, statement.location)
        loop = _Scope(scope)
        loop.define(_Binding(statement.var, "local", statement.location))
        self._block(statement.body, loop)

    def _function_body(self, statement: FunctionDeclaration, scope: _Scope) -> None:
        inner = _Scope(scope)
        for parameter in statement.parameters:
            self._shadow(parameter.name, parameter.location)
            inner.define(_Binding(parameter.name, "local", parameter.location))
        if statement.inline:
            assert isinstance(statement.body, Expression)
            self._expr(statement.body, inner)
        else:
            assert isinstance(statement.body, list)
            if not statement.body:
                self._finding(statement.location, "empty-block", f"empty function body '{statement.name}'")
            else:
                self._block(statement.body, inner)
                return
        self._report_unused(inner, set())

    def _expr(self, expression: Expression, scope: _Scope) -> None:
        if isinstance(expression, VariableExpression):
            scope.mark_used(expression.name)
            return
        if isinstance(expression, BinaryExpression):
            self._comparison_to_bool(expression)
            self._expr(expression.left, scope)
            self._expr(expression.right, scope)
            return
        if isinstance(expression, UnaryExpression):
            self._expr(expression.operand, scope)
            return
        if isinstance(expression, CallExpression):
            self._call(expression, scope)
            return
        if isinstance(expression, MemberExpression):
            self._expr(expression.object, scope)
            return
        if isinstance(expression, IndexExpression):
            self._expr(expression.target, scope)
            self._expr(expression.index, scope)
            return
        if isinstance(expression, ListLiteral):
            for element in expression.elements:
                self._expr(element, scope)
            return
        if isinstance(expression, HashLiteral):
            for pair in expression.pairs:
                self._expr(pair.value, scope)
            return
        if isinstance(expression, StringInterpolation):
            for part in expression.parts:
                self._expr(part, scope)
            return
        if isinstance(expression, (LiteralExpression, StringLiteralExpression)):
            return

    def _call(self, expression: CallExpression, scope: _Scope) -> None:
        callee = expression.callee
        if isinstance(callee, VariableExpression):
            scope.mark_used(callee.name)
            if callee.name == "order" and len(expression.arguments) >= 2:
                self._mark_order_comparator(expression.arguments[1].value, scope)
        elif isinstance(callee, MemberExpression):
            self._expr(callee.object, scope)
            if callee.name == "order" and expression.arguments:
                self._mark_order_comparator(expression.arguments[0].value, scope)
        else:
            self._expr(callee, scope)
        for argument in expression.arguments:
            self._expr(argument.value, scope)

    def _mark_order_comparator(self, expression: Expression, scope: _Scope) -> None:
        if isinstance(expression, StringLiteralExpression) and isinstance(expression.value, str):
            scope.mark_used(expression.value)

    def _test_naming(self, function: FunctionDeclaration) -> None:
        if not _looks_like_test_name(function.name):
            return
        if _is_test_xxx_unit(function.name, len(function.parameters)):
            return
        self._finding(
            function.location,
            "test-naming",
            f"function '{function.name}' looks like a test but is not a zero-arg testXxx entry",
        )

    def _self_assign(self, statement: AssignmentStatement) -> None:
        value = statement.value
        if isinstance(value, VariableExpression) and value.name == statement.name:
            self._finding(statement.location, "self-assign", f"self-assignment of '{statement.name}'")
            return
        if not isinstance(value, BinaryExpression) or value.operator.type is not TokenType.PLUS:
            return
        left, right = value.left, value.right
        same_plus_zero = _is_name(left, statement.name) and _is_numeric_zero(right)
        zero_plus_same = _is_numeric_zero(left) and _is_name(right, statement.name)
        if same_plus_zero or zero_plus_same:
            self._finding(statement.location, "self-assign", f"self-assignment of '{statement.name}'")

    def _unreachable(self, statements: list[Statement]) -> None:
        terminator: str | None = None
        for statement in statements:
            if terminator is not None:
                self._finding(
                    statement.location,
                    "unreachable-after-fail",
                    f"unreachable code after {terminator}",
                )
                continue
            terminator = _exits_block(statement)

    def _comparison_to_bool(self, expression: BinaryExpression) -> None:
        if expression.operator.type not in {TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL}:
            return
        if self._is_bool_literal(expression.left) or self._is_bool_literal(expression.right):
            self._finding(
                expression.location,
                "comparison-to-bool",
                "comparison to a boolean literal; use the value directly",
            )

    def _shadow(self, name: str, location: SourceLocation) -> None:
        if name in self._builtins:
            self._finding(location, "shadow-builtin", f"'{name}' shadows a builtin")

    def _report_unused(self, scope: _Scope, exported: set[str]) -> None:
        for binding in scope.bindings.values():
            if binding.used or binding.name in exported:
                continue
            if binding.kind == "function":
                self._finding(binding.location, "unused-function", f"unused function '{binding.name}'")
            elif binding.kind == "import":
                self._finding(binding.location, "unused-import", f"unused import '{binding.name}'")
            else:
                self._finding(binding.location, "unused-local", f"unused local '{binding.name}'")

    def _finding(self, location: SourceLocation, rule: str, message: str) -> None:
        self._findings.append(
            LintFinding(
                path=self._filename,
                line=location.line,
                column=location.column,
                rule=rule,
                message=message,
            )
        )

    @staticmethod
    def _function_of(statement: Statement) -> FunctionDeclaration | None:
        if isinstance(statement, FunctionDeclaration):
            return statement
        if isinstance(statement, ExportDeclaration) and isinstance(statement.declaration, FunctionDeclaration):
            return statement.declaration
        return None

    @staticmethod
    def _is_bool_literal(expression: Expression) -> bool:
        return isinstance(expression, LiteralExpression) and isinstance(expression.value, bool)

    @staticmethod
    def _redundant_by_one(statement: ForStatement) -> bool:
        step = statement.step
        if not isinstance(step, LiteralExpression) or isinstance(step.value, bool) or step.value != 1:
            return False
        return step.location != statement.end.location


def _looks_like_test_name(name: str) -> bool:
    return len(name) >= 4 and name[:4].lower() == "test"


def _is_test_xxx_name(name: str) -> bool:
    if not name.startswith("test"):
        return False
    return len(name) == 4 or not name[4].islower()


def _is_test_xxx_unit(name: str, parameter_count: int) -> bool:
    return parameter_count == 0 and _is_test_xxx_name(name)


def _is_name(expression: Expression, name: str) -> bool:
    return isinstance(expression, VariableExpression) and expression.name == name


def _is_numeric_zero(expression: Expression) -> bool:
    if not isinstance(expression, LiteralExpression) or isinstance(expression.value, bool):
        return False
    return expression.value == 0


def _is_fail_call(expression: Expression) -> bool:
    if not isinstance(expression, CallExpression):
        return False
    callee = expression.callee
    return isinstance(callee, VariableExpression) and callee.name == "fail"


def _exits_block(statement: Statement) -> str | None:
    if isinstance(statement, ReturnStatement):
        return "return"
    if isinstance(statement, ExpressionStatement) and _is_fail_call(statement.expression):
        return "fail"
    return None
