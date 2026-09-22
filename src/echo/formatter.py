from __future__ import annotations

from echo.frontend.ast.nodes import (
    Argument,
    AssignmentStatement,
    BinaryExpression,
    BreakStatement,
    CallExpression,
    ClassConstruction,
    ClassDeclaration,
    ClassType,
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
    InterfaceDeclaration,
    InterfaceType,
    LambdaExpression,
    ListLiteral,
    ListPattern,
    LiteralExpression,
    LiteralPattern,
    MemberAssignment,
    MemberCompoundAssignment,
    MemberExpression,
    NamePattern,
    ObjectType,
    Parameter,
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
    TypeAnnotation,
    TypeName,
    TypePattern,
    UnaryExpression,
    UnionType,
    UseStatement,
    VariableDeclaration,
    VariableExpression,
    WatchStatement,
    WhileStatement,
)
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.frontend.tokens import KEYWORDS, Token, TokenType


PREC_OR = 1
PREC_AND = 2
PREC_EQ = 3
PREC_CMP = 4
PREC_RANGE = 5
PREC_TERM = 6
PREC_FACTOR = 7
PREC_UNARY = 8
PREC_POSTFIX = 9
PREC_PRIMARY = 10

_BIN_PREC = {
    TokenType.OR_OR: PREC_OR,
    TokenType.AND_AND: PREC_AND,
    TokenType.EQUAL_EQUAL: PREC_EQ,
    TokenType.BANG_EQUAL: PREC_EQ,
    TokenType.LESS: PREC_CMP,
    TokenType.LESS_EQUAL: PREC_CMP,
    TokenType.GREATER: PREC_CMP,
    TokenType.GREATER_EQUAL: PREC_CMP,
    TokenType.PLUS: PREC_TERM,
    TokenType.MINUS: PREC_TERM,
    TokenType.STAR: PREC_FACTOR,
    TokenType.SLASH: PREC_FACTOR,
    TokenType.PERCENT: PREC_FACTOR,
}


def format_source(source: str, filename: str = "<input>") -> str:
    tokens = Lexer().tokenize(source, filename=filename)
    comments = [token for token in tokens if token.type is TokenType.COMMENT]
    program = Parser(tokens).parse()
    return _Printer(comments).print_program(program)


class _Printer:
    def __init__(self, comments: list[Token]) -> None:
        self._comments = comments
        self._comment_index = 0
        self._indent = 0
        self._lines: list[str] = []
        self._current = ""

    def print_program(self, program: Program) -> str:
        for statement in program.statements:
            self._leading_comments(statement.location.line)
            self._statement(statement)
            self._trailing_comments(statement.location.line)
        self._flush_remaining_comments()
        text = "\n".join(self._lines)
        if self._current:
            text = f"{text}\n{self._current}" if text else self._current
        if text and not text.endswith("\n"):
            text += "\n"
        return text

    def _statement(self, statement: Statement) -> None:
        if isinstance(statement, VariableDeclaration):
            prefix = "const " if statement.const else ""
            self._line(
                f"{prefix}{statement.name}: {self._type(statement.declared_type)} = {self._expr(statement.initializer)};"
            )
            return
        if isinstance(statement, DestructureDeclaration):
            prefix = "const " if statement.const else ""
            self._line(
                f"{prefix}{self._pattern(statement.pattern)} = {self._expr(statement.initializer)};"
            )
            return
        if isinstance(statement, DestructureAssignment):
            self._line(f"{self._pattern(statement.pattern)} = {self._expr(statement.value)};")
            return
        if isinstance(statement, AssignmentStatement):
            self._line(f"{statement.name} = {self._expr(statement.value)};")
            return
        if isinstance(statement, CompoundAssignment):
            self._line(f"{statement.name} {statement.operator.lexeme} {self._expr(statement.value)};")
            return
        if isinstance(statement, IndexAssignment):
            path = "".join(f"[{self._expr(index)}]" for index in statement.indices)
            self._line(f"{statement.name}{path} = {self._expr(statement.value)};")
            return
        if isinstance(statement, MemberAssignment):
            self._line(
                f"{self._expr(statement.object)}.{statement.name} = {self._expr(statement.value)};"
            )
            return
        if isinstance(statement, MemberCompoundAssignment):
            self._line(
                f"{self._expr(statement.object)}.{statement.name} {statement.operator.lexeme} "
                f"{self._expr(statement.value)};"
            )
            return
        if isinstance(statement, ExpressionStatement):
            self._line(f"{self._expr(statement.expression)};")
            return
        if isinstance(statement, ReturnStatement):
            if statement.value is None:
                self._line("return;")
            else:
                self._line(f"return {self._expr(statement.value)};")
            return
        if isinstance(statement, BreakStatement):
            self._line("break;")
            return
        if isinstance(statement, ContinueStatement):
            self._line("continue;")
            return
        if isinstance(statement, UseStatement):
            prefix = "use mut " if statement.mutable else "use "
            self._line(f"{prefix}{', '.join(statement.names)};")
            return
        if isinstance(statement, WatchStatement):
            self._line(f"watch {', '.join(statement.names)};")
            return
        if isinstance(statement, TypeAliasStatement):
            self._line(f"type {statement.name} = {self._type(statement.target)};")
            return
        if isinstance(statement, ClassDeclaration):
            self._write(f"class {statement.name}")
            if statement.implements:
                self._write(f" implements {', '.join(statement.implements)}")
            self._write(" ")
            self._write("{")
            self._newline()
            self._indent += 1
            if statement.fields:
                self._line("new {")
                self._indent += 1
                for field in statement.fields:
                    line = f"{field.name}: {self._type(field.type)}"
                    if field.default is not None:
                        line += f" = {self._expr(field.default)}"
                    self._line(f"{line};")
                self._indent -= 1
                self._line("}")
            for method in statement.methods:
                self._function(method)
            self._indent -= 1
            self._write("}")
            self._newline()
            return
        if isinstance(statement, InterfaceDeclaration):
            self._write(f"interface {statement.name} ")
            self._write("{")
            self._newline()
            self._indent += 1
            for method in statement.methods:
                params = ", ".join(self._param(param) for param in method.parameters)
                self._line(f"fn {method.name}({params}) -> {self._type(method.return_type)};")
            self._indent -= 1
            self._write("}")
            self._newline()
            return
        if isinstance(statement, ImportDeclaration):
            self._line(f'import {statement.name} from "{statement.module}";')
            return
        if isinstance(statement, ExportDeclaration):
            if statement.declaration is None:
                self._line(f"export {statement.name};")
                return
            self._write("export ")
            self._statement(statement.declaration)
            return
        if isinstance(statement, FunctionDeclaration):
            self._function(statement)
            return
        if isinstance(statement, IfStatement):
            self._if_statement(statement, leading="if")
            return
        if isinstance(statement, SwitchStatement):
            self._switch_statement(statement)
            return
        if isinstance(statement, WhileStatement):
            self._write(f"while {self._expr(statement.condition)} ")
            self._block(statement.body)
            return
        if isinstance(statement, ForStatement):
            dots = ".." if statement.inclusive else "..."
            header = f"for {statement.var}: {self._type(statement.var_type)} in {self._expr(statement.start)}{dots}{self._expr(statement.end)}"
            if not (
                isinstance(statement.step, LiteralExpression)
                and not isinstance(statement.step.value, bool)
                and statement.step.value == 1
            ):
                header += f" by {self._expr(statement.step)}"
            self._write(f"{header} ")
            self._block(statement.body)
            return
        if isinstance(statement, ForeachStatement):
            self._write(
                f"foreach {statement.var}: {self._type(statement.var_type)} in {self._expr(statement.iterable)} "
            )
            self._block(statement.body)
            return
        raise TypeError(f"unhandled statement: {type(statement).__name__}")

    def _function(self, statement: FunctionDeclaration) -> None:
        params = ", ".join(self._param(param) for param in statement.parameters)
        header = f"fn {statement.name}({params})"
        if statement.return_type is not None:
            header += f" -> {self._type(statement.return_type)}"
        if statement.inline:
            assert isinstance(statement.body, Expression)
            self._line(f"{header} => {self._expr(statement.body)};")
            return
        self._write(f"{header} ")
        assert isinstance(statement.body, list)
        self._block(statement.body)

    def _if_statement(self, statement: IfStatement, *, leading: str) -> None:
        self._write(f"{leading} {self._expr(statement.condition)} ")
        self._block(statement.then_branch, newline_after=False)
        if statement.else_branch is None:
            self._newline()
            return
        if len(statement.else_branch) == 1 and isinstance(statement.else_branch[0], IfStatement):
            self._write(" else ")
            self._if_statement(statement.else_branch[0], leading="if")
            return
        self._write(" else ")
        self._block(statement.else_branch)

    def _switch_statement(self, statement: SwitchStatement) -> None:
        self._write(f"switch {self._expr(statement.discriminant)} ")
        self._write("{")
        self._newline()
        self._indent += 1
        for arm in statement.arms:
            if arm.pattern is None:
                self._write("else ")
            else:
                self._write(f"{self._pattern(arm.pattern)} ")
            self._block(arm.body)
        self._indent -= 1
        self._write("}")
        self._newline()

    def _block(self, statements: list[Statement], *, newline_after: bool = True) -> None:
        self._write("{")
        self._newline()
        self._indent += 1
        for statement in statements:
            self._leading_comments(statement.location.line)
            self._statement(statement)
            self._trailing_comments(statement.location.line)
        self._flush_inner_comments()
        self._indent -= 1
        self._write("}")
        if newline_after:
            self._newline()

    def _expr(self, expression: Expression, min_prec: int = 0) -> str:
        text = self._expr_raw(expression)
        if self._prec(expression) < min_prec:
            return f"({text})"
        return text

    def _expr_raw(self, expression: Expression) -> str:
        if isinstance(expression, LiteralExpression):
            return self._literal(expression.value)
        if isinstance(expression, StringLiteralExpression):
            return self._wrap_string(expression.value)
        if isinstance(expression, StringInterpolation):
            return self._interpolation(expression)
        if isinstance(expression, VariableExpression):
            return expression.name
        if isinstance(expression, UnaryExpression):
            operand = self._expr(expression.operand, PREC_UNARY)
            return f"{expression.operator.lexeme}{operand}"
        if isinstance(expression, BinaryExpression):
            prec = _BIN_PREC[expression.operator.type]
            left = self._expr(expression.left, prec)
            right = self._expr(expression.right, prec + 1)
            return f"{left} {expression.operator.lexeme} {right}"
        if isinstance(expression, CallExpression):
            callee = self._expr(expression.callee, PREC_POSTFIX)
            args = ", ".join(self._argument(arg) for arg in expression.arguments)
            return f"{callee}({args})"
        if isinstance(expression, MemberExpression):
            return f"{self._expr(expression.object, PREC_POSTFIX)}.{expression.name}"
        if isinstance(expression, ClassConstruction):
            inner = ", ".join(f"{name}: {self._expr(value)}" for name, value in expression.fields)
            return f"{expression.class_name} {{{inner}}}" if inner else f"{expression.class_name} {{}}"
        if isinstance(expression, IndexExpression):
            return f"{self._expr(expression.target, PREC_POSTFIX)}[{self._expr(expression.index)}]"
        if isinstance(expression, SliceExpression):
            start = self._expr(expression.start) if expression.start is not None else ""
            end = self._expr(expression.end) if expression.end is not None else ""
            return f"{self._expr(expression.target, PREC_POSTFIX)}[{start}:{end}]"
        if isinstance(expression, RangeExpression):
            dots = ".." if expression.inclusive else "..."
            text = f"{self._expr(expression.start, PREC_RANGE + 1)}{dots}{self._expr(expression.end, PREC_RANGE + 1)}"
            if not (
                isinstance(expression.step, LiteralExpression)
                and not isinstance(expression.step.value, bool)
                and expression.step.value == 1
            ):
                text += f" by {self._expr(expression.step, PREC_RANGE + 1)}"
            return text
        if isinstance(expression, LambdaExpression):
            return self._lambda(expression)
        if isinstance(expression, ListLiteral):
            return f"[{', '.join(self._expr(item) for item in expression.elements)}]"
        if isinstance(expression, HashLiteral):
            pairs = ", ".join(f"{self._hash_key(pair.key)}: {self._expr(pair.value)}" for pair in expression.pairs)
            return f"{{{pairs}}}" if pairs else "{}"
        raise TypeError(f"unhandled expression: {type(expression).__name__}")

    def _prec(self, expression: Expression) -> int:
        if isinstance(expression, RangeExpression):
            return PREC_RANGE
        if isinstance(expression, BinaryExpression):
            return _BIN_PREC[expression.operator.type]
        if isinstance(expression, UnaryExpression):
            return PREC_UNARY
        if isinstance(expression, (CallExpression, MemberExpression, IndexExpression, SliceExpression)):
            return PREC_POSTFIX
        if isinstance(expression, LambdaExpression):
            return PREC_PRIMARY
        return PREC_PRIMARY

    def _argument(self, argument: Argument) -> str:
        value = self._expr(argument.value)
        if argument.name:
            return f"{argument.name}: {value}"
        return value

    def _param(self, parameter: Parameter) -> str:
        if parameter.pattern is not None:
            text = self._pattern(parameter.pattern)
            return f"const {text}" if parameter.const else text
        if parameter.name == "this":
            return "this"
        text = f"{parameter.name}: {self._type(parameter.type)}"
        if parameter.variadic:
            text += "..."
        if parameter.default is not None:
            text += f" = {self._expr(parameter.default)}"
        if parameter.const:
            text = f"const {text}"
        return text

    def _pattern(self, pattern: Pattern) -> str:
        if isinstance(pattern, LiteralPattern):
            if isinstance(pattern.value, str):
                return self._wrap_string(pattern.value)
            return self._literal(pattern.value)
        if isinstance(pattern, TypePattern):
            text = self._type(pattern.type)
            if pattern.binding is not None:
                text += f" {pattern.binding}"
            return text
        if isinstance(pattern, NamePattern):
            text = pattern.name
            if pattern.key is not None:
                text = f"{pattern.key} as {pattern.name}"
            if pattern.declared_type is not None:
                text += f": {self._type(pattern.declared_type)}"
            if pattern.rest:
                text += "..."
            return text
        if isinstance(pattern, ListPattern):
            inner = ", ".join(self._pattern(element) for element in pattern.elements)
            return f"[{inner}]"
        if isinstance(pattern, HashPattern):
            inner = ", ".join(self._pattern(field) for field in pattern.fields)
            return f"{{{inner}}}" if inner else "{}"
        raise TypeError(f"unhandled pattern: {type(pattern).__name__}")

    def _lambda(self, expression: LambdaExpression) -> str:
        params = ", ".join(self._param(param) for param in expression.parameters)
        header = f"fn({params})"
        if expression.return_type is not None:
            header += f" -> {self._type(expression.return_type)}"
        if expression.inline:
            assert isinstance(expression.body, Expression)
            return f"{header} => {self._expr(expression.body)}"
        assert isinstance(expression.body, list)
        inner = self._flatten_statements(expression.body)
        return f"{header} {{ {inner} }}" if inner else f"{header} {{}}"

    def _flatten_statements(self, statements: list[Statement]) -> str:
        nested = _Printer([])
        for statement in statements:
            nested._statement(statement)
        text = "\n".join(nested._lines)
        if nested._current:
            text = f"{text}\n{nested._current}" if text else nested._current
        return " ".join(line.strip() for line in text.splitlines() if line.strip())

    def _type(self, annotation: TypeAnnotation) -> str:
        if isinstance(annotation, TypeName):
            return annotation.name
        if isinstance(annotation, ClassType):
            return annotation.name
        if isinstance(annotation, InterfaceType):
            return annotation.name
        if isinstance(annotation, UnionType):
            return " | ".join(self._type(member) for member in annotation.members)
        if isinstance(annotation, FunctionType):
            params = []
            for index, param_type in enumerate(annotation.param_types):
                suffix = "..." if annotation.variadic and index == len(annotation.param_types) - 1 else ""
                params.append(f"{self._type(param_type)}{suffix}")
            return f"fn({', '.join(params)}) -> {self._type(annotation.return_type)}"
        if isinstance(annotation, ObjectType):
            fields = ", ".join(f"{name}: {self._type(field)}" for name, field in annotation.fields.items())
            object_type = f"{{{fields}}}" if fields else "{}"
            return f"exact {object_type}" if annotation.exact else object_type
        raise TypeError(f"unhandled type: {type(annotation).__name__}")

    def _literal(self, value: object) -> str:
        if value is None:
            return "null"
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        if isinstance(value, float):
            text = repr(value)
            if text.endswith(".0"):
                return text
            return str(value) if "e" not in text.lower() else text
        return str(value)

    def _wrap_string(self, raw: str) -> str:
        if "\n" in raw:
            if '"""' not in raw:
                return f'"""{raw}"""'
            return f"'''{raw}'''"
        return f'"{raw}"'

    def _interpolation(self, expression: StringInterpolation) -> str:
        body = ""
        for part in expression.parts:
            if isinstance(part, StringLiteralExpression):
                body += part.value
            else:
                body += f"${{{self._expr(part)}}}"
        return self._wrap_string(body)

    def _hash_key(self, key: str) -> str:
        if key.isidentifier() and key not in KEYWORDS:
            return key
        return f'"{key}"'

    def _leading_comments(self, line: int) -> None:
        while self._comment_index < len(self._comments):
            comment = self._comments[self._comment_index]
            if comment.line >= line:
                break
            self._comment_line(comment)
            self._comment_index += 1

    def _trailing_comments(self, line: int) -> None:
        while self._comment_index < len(self._comments):
            comment = self._comments[self._comment_index]
            if comment.line != line:
                break
            if self._lines:
                self._lines[-1] = f"{self._lines[-1]} {comment.lexeme}"
            else:
                self._line(comment.lexeme)
            self._comment_index += 1

    def _flush_inner_comments(self) -> None:
        min_column = self._indent * 4 + 1
        while self._comment_index < len(self._comments):
            comment = self._comments[self._comment_index]
            if comment.column < min_column:
                break
            self._comment_line(comment)
            self._comment_index += 1

    def _flush_remaining_comments(self) -> None:
        while self._comment_index < len(self._comments):
            self._comment_line(self._comments[self._comment_index])
            self._comment_index += 1

    def _comment_line(self, comment: Token) -> None:
        text = comment.lexeme
        if "\n" in text:
            for index, piece in enumerate(text.splitlines()):
                self._line(piece if index == 0 or piece.startswith("*") or piece.startswith("/*") else piece)
            return
        self._line(text)

    def _write(self, text: str) -> None:
        if not self._current:
            self._current = ("    " * self._indent) + text
        else:
            self._current += text

    def _newline(self) -> None:
        self._lines.append(self._current.rstrip())
        self._current = ""

    def _line(self, text: str) -> None:
        self._write(text)
        self._newline()
