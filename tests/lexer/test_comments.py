from echo.errors import LexError
from echo.frontend.lexer import Lexer
from echo.frontend.tokens import TokenType


def test_block_comment_is_skipped():
    tokens = Lexer().tokenize("/* hidden\nstill hidden */\nsay(1);\n")
    assert any(token.lexeme == "say" for token in tokens)
    assert tokens[-1].type == TokenType.EOF


def test_unterminated_block_comment_is_an_error():
    try:
        Lexer().tokenize("say(1);\n/* never closed\n")
        assert False, "expected LexError"
    except LexError as exc:
        assert "Unterminated block comment" in exc.message
