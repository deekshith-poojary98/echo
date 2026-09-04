from echo.frontend.lexer import Lexer
from echo.frontend.tokens import TokenType


def tokenize(source: str):
    return Lexer().tokenize(source)


def token_pairs(source: str) -> list[tuple[TokenType, str]]:
    return [(token.type, token.lexeme) for token in tokenize(source) if token.type != TokenType.EOF]


def test_import_tokens():
    assert token_pairs('import add from "math";') == [
        (TokenType.IMPORT, "import"),
        (TokenType.IDENTIFIER, "add"),
        (TokenType.FROM, "from"),
        (TokenType.STRING, "math"),
        (TokenType.SEMICOLON, ";"),
    ]


def test_export_name_tokens():
    assert token_pairs("export add;") == [
        (TokenType.EXPORT, "export"),
        (TokenType.IDENTIFIER, "add"),
        (TokenType.SEMICOLON, ";"),
    ]


def test_module_name_is_a_string_not_a_keyword():
    types = [token.type for token in tokenize('import add from "math";') if token.type != TokenType.EOF]
    assert TokenType.IDENTIFIER not in types[3:]
    assert types[3] == TokenType.STRING


def test_use_tokens_are_unchanged():
    assert token_pairs("use mut x;") == [
        (TokenType.USE, "use"),
        (TokenType.MUT, "mut"),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.SEMICOLON, ";"),
    ]
