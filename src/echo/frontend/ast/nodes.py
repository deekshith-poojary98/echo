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
    exact: bool = False


@dataclass
class FunctionType(TypeAnnotation):
    param_types: list[TypeAnnotation]
    return_type: TypeAnnotation
    variadic: bool = False


@dataclass
class UnionType(TypeAnnotation):
    """Flattened union of type members (`int | str`). Always has 2+ members."""

    members: list[TypeAnnotation]


@dataclass
class Pattern(Node):
    pass


@dataclass
class NamePattern(Pattern):
    name: str
    declared_type: TypeAnnotation | None = None
    rest: bool = False
    key: str | None = None  # hash source key when renamed; None means key == name
    rest_container: str | None = None  # "list" or "hash" when rest

    def source_key(self) -> str:
        return self.key if self.key is not None else self.name


@dataclass
class ListPattern(Pattern):
    elements: list[Pattern]


@dataclass
class HashPattern(Pattern):
    fields: list[NamePattern]


@dataclass
class LiteralPattern(Pattern):
    value: object


@dataclass
class TypePattern(Pattern):
    type: TypeAnnotation
    binding: str | None = None


@dataclass
class SwitchArm(Node):
    pattern: Pattern | None
    body: list[Statement]


@dataclass
class SwitchStatement(Statement):
    discriminant: Expression
    arms: list[SwitchArm]


@dataclass
class Parameter:
    name: str
    type: TypeAnnotation
    location: SourceLocation
    default: Expression | None = None
    variadic: bool = False
    pattern: Pattern | None = None
    const: bool = False


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
class SliceExpression(Expression):
    target: Expression
    start: Expression | None
    end: Expression | None


@dataclass
class RangeExpression(Expression):
    start: Expression
    end: Expression
    step: Expression
    inclusive: bool


@dataclass
class LambdaExpression(Expression):
    parameters: list[Parameter]
    body: list[Statement] | Expression
    inline: bool
    return_type: TypeAnnotation | None = None


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
    const: bool = False


@dataclass
class AssignmentStatement(Statement):
    name: str
    value: Expression


@dataclass
class DestructureDeclaration(Statement):
    pattern: Pattern
    initializer: Expression
    const: bool = False


@dataclass
class DestructureAssignment(Statement):
    pattern: Pattern
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


@dataclass
class ImportDeclaration(Statement):
    name: str
    module: str


@dataclass
class ExportDeclaration(Statement):
    name: str
    declaration: FunctionDeclaration | VariableDeclaration | None = None


def iter_name_patterns(pattern: Pattern) -> list[NamePattern]:
    names: list[NamePattern] = []
    if isinstance(pattern, NamePattern):
        names.append(pattern)
    elif isinstance(pattern, ListPattern):
        for element in pattern.elements:
            names.extend(iter_name_patterns(element))
    elif isinstance(pattern, HashPattern):
        names.extend(pattern.fields)
    elif isinstance(pattern, TypePattern) and pattern.binding is not None:
        names.append(NamePattern(pattern.location, pattern.binding, pattern.type))
    return names


def list_pattern_fixed(pattern: ListPattern) -> list[Pattern]:
    if pattern.elements and isinstance(pattern.elements[-1], NamePattern) and pattern.elements[-1].rest:
        return pattern.elements[:-1]
    return pattern.elements


def list_pattern_rest(pattern: ListPattern) -> NamePattern | None:
    if pattern.elements and isinstance(pattern.elements[-1], NamePattern) and pattern.elements[-1].rest:
        return pattern.elements[-1]
    return None


def hash_pattern_fixed(pattern: HashPattern) -> list[NamePattern]:
    if pattern.fields and pattern.fields[-1].rest:
        return pattern.fields[:-1]
    return pattern.fields


def hash_pattern_rest(pattern: HashPattern) -> NamePattern | None:
    if pattern.fields and pattern.fields[-1].rest:
        return pattern.fields[-1]
    return None


def pattern_container_type(pattern: Pattern) -> str:
    if isinstance(pattern, ListPattern):
        return "list"
    if isinstance(pattern, HashPattern):
        return "hash"
    return "dynamic"
