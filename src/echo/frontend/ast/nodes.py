from __future__ import annotations

from dataclasses import dataclass

from echo.errors import SourceLocation
from echo.frontend.tokens import Token


@dataclass
class Node:
    location: SourceLocation


@dataclass
class Expression(Node):
    pass


@dataclass
class Statement(Node):
    pass


@dataclass
class TypeAnnotation(Node):
    pass


@dataclass
class TypeName(TypeAnnotation):
    name: str


@dataclass
class ObjectType(TypeAnnotation):
    fields: dict[str, TypeAnnotation]


@dataclass
class Parameter:
    name: str
    type: TypeAnnotation
    location: SourceLocation


@dataclass
class Argument:
    value: Expression
    location: SourceLocation
    name: str | None = None


@dataclass
class LiteralExpression(Expression):
    value: object


@dataclass
class StringLiteralExpression(Expression):
    value: str


@dataclass
class StringInterpolation(Expression):
    parts: list[Expression]


@dataclass
class VariableExpression(Expression):
    name: str


@dataclass
class BinaryExpression(Expression):
    left: Expression
    operator: Token
    right: Expression


@dataclass
class UnaryExpression(Expression):
    operator: Token
    operand: Expression


@dataclass
class CallExpression(Expression):
    callee: Expression
    arguments: list[Argument]


@dataclass
class MemberExpression(Expression):
    object: Expression
    name: str


@dataclass
class IndexExpression(Expression):
    target: Expression
    index: Expression


@dataclass
class ListLiteral(Expression):
    elements: list[Expression]


@dataclass
class HashPair:
    key: str
    value: Expression
    location: SourceLocation


@dataclass
class HashLiteral(Expression):
    pairs: list[HashPair]


@dataclass
class Program(Node):
    statements: list[Statement]


@dataclass
class ExpressionStatement(Statement):
    expression: Expression


@dataclass
class VariableDeclaration(Statement):
    name: str
    declared_type: TypeAnnotation
    initializer: Expression


@dataclass
class AssignmentStatement(Statement):
    name: str
    value: Expression


@dataclass
class CompoundAssignment(Statement):
    name: str
    operator: Token
    value: Expression


@dataclass
class IndexAssignment(Statement):
    name: str
    indices: list[Expression]
    value: Expression


@dataclass
class IfStatement(Statement):
    condition: Expression
    then_branch: list[Statement]
    else_branch: list[Statement] | None = None


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: list[Statement]


@dataclass
class ForStatement(Statement):
    var: str
    var_type: TypeAnnotation
    start: Expression
    end: Expression
    step: Expression
    inclusive: bool
    body: list[Statement]


@dataclass
class ForeachStatement(Statement):
    var: str
    var_type: TypeAnnotation
    iterable: Expression
    body: list[Statement]


@dataclass
class FunctionDeclaration(Statement):
    name: str
    parameters: list[Parameter]
    body: list[Statement] | Expression
    inline: bool
    return_type: TypeAnnotation | None = None


@dataclass
class ReturnStatement(Statement):
    value: Expression | None = None


@dataclass
class BreakStatement(Statement):
    pass


@dataclass
class ContinueStatement(Statement):
    pass


@dataclass
class UseStatement(Statement):
    names: list[str]
    mutable: bool


@dataclass
class WatchStatement(Statement):
    names: list[str]


@dataclass
class TypeAliasStatement(Statement):
    name: str
    target: TypeAnnotation
