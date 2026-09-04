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
