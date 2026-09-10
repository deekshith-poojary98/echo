from echo.frontend.lexer import Lexer
from echo.frontend.tokens import TokenType


def test_integer_and_float_and_range():
    tokens = Lexer().tokenize("1 2.5 1..10 1...10\n")
    types = [token.type for token in tokens if token.type != TokenType.EOF]
    assert types == [
        TokenType.INTEGER,
        TokenType.FLOAT,
        TokenType.INTEGER,
        TokenType.DOT_DOT,
        TokenType.INTEGER,
        TokenType.INTEGER,
        TokenType.DOT_DOT_DOT,
        TokenType.INTEGER,
    ]


def test_leading_dot_and_scientific():
    tokens = Lexer().tokenize(".5 1e3 1e-3 1E+2\n")
    values = [(token.type, token.lexeme) for token in tokens if token.type != TokenType.EOF]
    assert values == [
        (TokenType.FLOAT, ".5"),
        (TokenType.FLOAT, "1e3"),
        (TokenType.FLOAT, "1e-3"),
        (TokenType.FLOAT, "1E+2"),
    ]


def test_trailing_dot_stays_integer_then_dot():
    tokens = Lexer().tokenize("5.asInt()\n")
    types = [token.type for token in tokens if token.type != TokenType.EOF]
    assert types[0] == TokenType.INTEGER
    assert types[1] == TokenType.DOT
    assert tokens[0].lexeme == "5"
