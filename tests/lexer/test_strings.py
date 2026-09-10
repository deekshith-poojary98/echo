from echo.errors import LexError
from echo.frontend.lexer import Lexer
from echo.frontend.tokens import TokenType


def tokenize(source: str):
    return Lexer().tokenize(source)


def test_empty_and_plain_strings():
    tokens = tokenize('say(""); say("hi");\n')
    strings = [token.lexeme for token in tokens if token.type == TokenType.STRING]
    assert "" in strings
    assert "hi" in strings


def test_interpolation_can_start_a_string():
    tokens = tokenize('say("${name}");\n')
    types = [token.type for token in tokens]
    assert TokenType.INTERPOLATION_START in types
    assert TokenType.IDENTIFIER in types


def test_unterminated_string():
    try:
        tokenize('say("oops);\n')
        assert False, "expected LexError"
    except LexError as exc:
        assert "Unterminated string" in exc.message


def test_triple_quoted_multiline_string():
    tokens = tokenize('"""hello\nworld"""\n')
    strings = [token.lexeme for token in tokens if token.type == TokenType.STRING]
    assert strings == ["hello\nworld"]


def test_triple_single_quoted_multiline_string():
    tokens = tokenize("'''a\nb'''\n")
    strings = [token.lexeme for token in tokens if token.type == TokenType.STRING]
    assert strings == ["a\nb"]


def test_triple_quoted_interpolation():
    tokens = tokenize('"""hi ${name}"""\n')
    types = [token.type for token in tokens if token.type != TokenType.EOF]
    assert TokenType.INTERPOLATION_START in types
    assert TokenType.IDENTIFIER in types


def test_unterminated_triple_string():
    try:
        tokenize('"""oops\n')
        assert False, "expected LexError"
    except LexError as exc:
        assert "Unterminated string" in exc.message
