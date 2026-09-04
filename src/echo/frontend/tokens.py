from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from echo.errors import SourceLocation


class TokenType(Enum):
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    TYPE = auto()

    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    FN = auto()
    FOR = auto()
    IF = auto()
    ELSE = auto()
    FOREACH = auto()
    IN = auto()
    BY = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    WHILE = auto()
    USE = auto()
    MUT = auto()
    WATCH = auto()
    TYPE_KW = auto()
    IMPORT = auto()
    EXPORT = auto()
    FROM = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    AND_AND = auto()
    OR_OR = auto()
    BANG = auto()
    ARROW = auto()
    FAT_ARROW = auto()
    DOT = auto()
    DOT_DOT = auto()
    DOT_DOT_DOT = auto()
    PLUS_EQUAL = auto()
    MINUS_EQUAL = auto()
    STAR_EQUAL = auto()
    SLASH_EQUAL = auto()
    PERCENT_EQUAL = auto()

    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()

    INTERPOLATION_START = auto()
    INTERPOLATION_END = auto()

    EOF = auto()


KEYWORDS: dict[str, TokenType] = {
    "fn": TokenType.FN,
    "for": TokenType.FOR,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "foreach": TokenType.FOREACH,
    "in": TokenType.IN,
    "by": TokenType.BY,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "while": TokenType.WHILE,
    "use": TokenType.USE,
    "mut": TokenType.MUT,
    "watch": TokenType.WATCH,
    "type": TokenType.TYPE_KW,
    "import": TokenType.IMPORT,
    "export": TokenType.EXPORT,
    "from": TokenType.FROM,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
}

TYPE_NAMES = frozenset({"int", "float", "str", "bool", "dynamic", "list", "hash", "void"})

COMPOUND_OPS = {
    TokenType.PLUS_EQUAL,
    TokenType.MINUS_EQUAL,
    TokenType.STAR_EQUAL,
    TokenType.SLASH_EQUAL,
    TokenType.PERCENT_EQUAL,
}

BINARY_OPS = {
    TokenType.PLUS,
    TokenType.MINUS,
    TokenType.STAR,
    TokenType.SLASH,
    TokenType.PERCENT,
    TokenType.EQUAL_EQUAL,
    TokenType.BANG_EQUAL,
    TokenType.LESS,
    TokenType.LESS_EQUAL,
    TokenType.GREATER,
    TokenType.GREATER_EQUAL,
    TokenType.AND_AND,
    TokenType.OR_OR,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    filename: str | None = None

    @property
    def location(self) -> SourceLocation:
        return SourceLocation(self.line, self.column, self.filename)

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.lexeme!r}, line={self.line}, col={self.column})"
