from __future__ import annotations

from pathlib import Path

import pytest

from echo_lexer import Lexer, Token as LexerToken
from echo_parser import Parser, Token


def parser(tokens):
    return Parser(tokens)


def test_lexer_token_repr_and_string_parsing(tmp_path):
    token = LexerToken("NUMBER", "1", 2, 3)
    assert repr(token) == "Token(NUMBER, 1, line=2, col=3)"

    lexer = Lexer()
    assert lexer._find_string_end('"a\\"b"', 0, '"') == 5
    assert lexer._find_string_end('"${x}"', 0, '"') == 5
    assert lexer._find_string_end('"unterminated', 0, '"') == -1

    parts = lexer._tokenize_interpolation_expr("name + 1", 1, 5)
    assert [part.type for part in parts] == ["IDENTIFIER", "OPERATOR", "NUMBER"]

    source = tmp_path / "sample.echo"
    source.write_text('say("Hello ${name}");\n', encoding="utf-8")
    tokens = lexer.read_source(str(source))
    assert any(tok.type == "INTERPOLATION_START" for tok in tokens)


def test_lexer_error_paths(tmp_path):
    lexer = Lexer()

    unterminated = tmp_path / "unterminated.echo"
    unterminated.write_text('say("oops);\n', encoding="utf-8")
    with pytest.raises(SyntaxError, match="Unterminated string"):
        lexer.read_source(str(unterminated))

    bad_interp = tmp_path / "bad_interp.echo"
    bad_interp.write_text('say("Hello ${name");\n', encoding="utf-8")
    with pytest.raises(SyntaxError, match="Unterminated string"):
        lexer.read_source(str(bad_interp))

    invalid = tmp_path / "invalid.echo"
    invalid.write_text("@\n", encoding="utf-8")
    with pytest.raises(SyntaxError, match="Invalid token '@'"):
        lexer.read_source(str(invalid))

    comments = tmp_path / "comments.echo"
    comments.write_text("/* hidden\nstill hidden */\nsay(1);\n", encoding="utf-8")
    tokens = lexer.read_source(str(comments))
    assert any(tok.value == "say" for tok in tokens)


def test_parser_constructor_and_basic_token_helpers():
    p = parser(["NUMBER(1)"])
    assert repr(p.peek()) == "NUMBER(1)"
    assert p.match("NUMBER").value == "1"
    assert p.peek() is None

    with pytest.raises(SyntaxError, match="Invalid token format"):
        Parser(["BROKEN"])

    with pytest.raises(TypeError, match="Invalid token object"):
        Parser([object()])

    p2 = parser([])
    with pytest.raises(SyntaxError, match="Unexpected end of input"):
        p2.advance()
    with pytest.raises(SyntaxError, match="Unexpected end of input"):
        p2.consume()


def test_parser_message_and_name_helpers():
    p = parser([Token("INTERPOLATION_START", "${", 1, 2)])
    assert "Found '${' outside a string" in p._unexpected_token_msg(p.peek())

    p = parser([Token("INTERPOLATION_END", "}", 1, 2)])
    assert "outside a string interpolation" in p._unexpected_token_msg(p.peek())

    p = parser([Token("PUNCTUATION", ";", 1, 2)])
    assert "Unexpected ';' here" in p._unexpected_token_msg(p.peek())

    p = parser([Token("IDENTIFIER", "x", 3, 4)])
    assert p._line_info(p.peek()) == " at line 3, column 4"
    assert p._peek_offset(0).value == "x"
    assert p._peek_offset(1) is None
    assert p._is_name_token(p.peek()) is True
    assert p._is_callable_type_keyword(Token("KEYWORD", "type")) is True
    assert p._is_method_token(Token("METHOD", "say")) is True
    assert p._expect_name() == "x"

    p = parser([Token("NUMBER", "1", 1, 1)])
    with pytest.raises(SyntaxError, match="Expected identifier"):
        p._expect_name()


def test_parser_type_and_arg_parsing_errors():
    p = parser([])
    with pytest.raises(SyntaxError, match="Expected type, got end of input"):
        p._parse_type_name()

    p = parser([Token("IDENTIFIER", "Alias", 1, 1)])
    with pytest.raises(SyntaxError, match="Unknown type alias 'Alias'"):
        p._parse_type_name()

    p = parser([Token("DATATYPE", "int", 1, 1)])
    assert p._parse_type_name() == "int"

    p = parser([
        Token("PUNCTUATION", "{", 1, 1),
        Token("IDENTIFIER", "id", 1, 2),
        Token("PUNCTUATION", ":", 1, 4),
        Token("DATATYPE", "int", 1, 5),
        Token("PUNCTUATION", "}", 1, 8),
    ])
    assert p._parse_object_type_spec() == {"kind": "object", "fields": {"id": "int"}}

    p = parser([
        Token("IDENTIFIER", "name", 1, 1),
        Token("PUNCTUATION", ":", 1, 5),
        Token("STRING", '"Echo"', 1, 7),
        Token("PUNCTUATION", ",", 1, 13),
        Token("NUMBER", "1", 1, 15),
        Token("PUNCTUATION", ")", 1, 16),
    ])
    with pytest.raises(SyntaxError, match="Positional arguments cannot appear after keyword arguments"):
        p._parse_arg_list()

    p = parser([Token("PUNCTUATION", ";", 1, 1), Token("PUNCTUATION", ")", 1, 2)])
    with pytest.raises(SyntaxError, match="Found ';' inside a function call"):
        p._parse_arg_list()


def test_parser_statement_and_expression_parsing():
    p = parser([
        Token("METHOD", "say", 1, 1),
        Token("PUNCTUATION", "(", 1, 4),
        Token("NUMBER", "1", 1, 5),
        Token("PUNCTUATION", ")", 1, 6),
        Token("PUNCTUATION", ";", 1, 7),
    ])
    stmt = p.parse_statement()
    assert stmt["type"] == "method_call"

    p = parser([
        Token("IDENTIFIER", "nums", 1, 1),
        Token("METHOD_OPERATOR", ".", 1, 5),
        Token("METHOD", "push", 1, 6),
        Token("PUNCTUATION", "(", 1, 10),
        Token("NUMBER", "1", 1, 11),
        Token("PUNCTUATION", ")", 1, 12),
        Token("METHOD_OPERATOR", ".", 1, 13),
        Token("METHOD", "length", 1, 14),
        Token("PUNCTUATION", "(", 1, 20),
        Token("PUNCTUATION", ")", 1, 21),
        Token("PUNCTUATION", ";", 1, 22),
    ])
    chained = p.parse_assignment_or_expr()
    assert chained["method"] == "length"
    assert chained["target"]["method"] == "push"

    p = parser([
        Token("IDENTIFIER", "grid", 1, 1),
        Token("PUNCTUATION", "[", 1, 5), Token("NUMBER", "0", 1, 6), Token("PUNCTUATION", "]", 1, 7),
        Token("PUNCTUATION", "[", 1, 8), Token("NUMBER", "1", 1, 9), Token("PUNCTUATION", "]", 1, 10),
        Token("OPERATOR", "=", 1, 12), Token("NUMBER", "5", 1, 14), Token("PUNCTUATION", ";", 1, 15),
    ])
    index_assign = p.parse_assignment_or_expr()
    assert index_assign["type"] == "index_assign"
    assert len(index_assign["indices"]) == 2

    p = parser([Token("PUNCTUATION", ";", 1, 1)])
    with pytest.raises(SyntaxError, match="Unexpected ';' here"):
        p.parse_primary()


def test_parser_function_loop_and_alias_forms():
    p = parser([
        Token("KEYWORD", "fn", 1, 1), Token("IDENTIFIER", "add", 1, 4), Token("PUNCTUATION", "(", 1, 7),
        Token("IDENTIFIER", "a", 1, 8), Token("PUNCTUATION", ":", 1, 9), Token("DATATYPE", "int", 1, 10),
        Token("PUNCTUATION", ",", 1, 13),
        Token("IDENTIFIER", "b", 1, 15), Token("PUNCTUATION", ":", 1, 16), Token("DATATYPE", "int", 1, 17),
        Token("PUNCTUATION", ")", 1, 20), Token("RETURN_TYPE", "->", 1, 22), Token("DATATYPE", "int", 1, 25),
        Token("OPERATOR", "=>", 1, 29), Token("IDENTIFIER", "a", 1, 32), Token("OPERATOR", "+", 1, 34), Token("IDENTIFIER", "b", 1, 36),
        Token("PUNCTUATION", ";", 1, 37),
    ])
    func = p.parse_function()
    assert func["inline"] is True

    p = parser([
        Token("KEYWORD", "fn", 1, 1), Token("IDENTIFIER", "bad", 1, 4), Token("PUNCTUATION", "(", 1, 7),
        Token("IDENTIFIER", "a", 1, 8), Token("PUNCTUATION", ")", 1, 9), Token("PUNCTUATION", "{", 1, 11), Token("PUNCTUATION", "}", 1, 12),
    ])
    with pytest.raises(SyntaxError, match="Type annotation required for parameter 'a'"):
        p.parse_function()

    p = parser([
        Token("KEYWORD", "fn", 1, 1), Token("IDENTIFIER", "bad", 1, 4), Token("PUNCTUATION", "(", 1, 7), Token("PUNCTUATION", ")", 1, 8),
        Token("PUNCTUATION", "{", 1, 10), Token("KEYWORD", "return", 1, 11), Token("NUMBER", "1", 1, 18), Token("PUNCTUATION", ";", 1, 19), Token("PUNCTUATION", "}", 1, 20),
    ])
    with pytest.raises(SyntaxError, match="Return type annotation required"):
        p.parse_function()

    p = parser([
        Token("KEYWORD", "for", 1, 1), Token("IDENTIFIER", "i", 1, 5), Token("PUNCTUATION", ":", 1, 6), Token("DATATYPE", "int", 1, 7),
        Token("KEYWORD", "in", 1, 11), Token("NUMBER", "3", 1, 14), Token("RANGE_OPERATOR", "..", 1, 15), Token("NUMBER", "1", 1, 17),
        Token("KEYWORD", "by", 1, 19), Token("OPERATOR", "-", 1, 22), Token("NUMBER", "1", 1, 23),
        Token("PUNCTUATION", "{", 1, 25), Token("PUNCTUATION", "}", 1, 26),
    ])
    loop = p.parse_for_loop()
    assert loop["by"] == -1

    p = parser([
        Token("KEYWORD", "foreach", 1, 1), Token("IDENTIFIER", "item", 1, 9), Token("PUNCTUATION", ":", 1, 13), Token("DATATYPE", "int", 1, 14),
        Token("KEYWORD", "in", 1, 18), Token("IDENTIFIER", "items", 1, 21), Token("PUNCTUATION", "{", 1, 27), Token("PUNCTUATION", "}", 1, 28),
    ])
    assert p.parse_foreach()["type"] == "foreach"

    p = parser([
        Token("KEYWORD", "type", 1, 1), Token("IDENTIFIER", "Age", 1, 6), Token("OPERATOR", "=", 1, 10), Token("DATATYPE", "int", 1, 12), Token("PUNCTUATION", ";", 1, 15),
    ])
    assert p.parse_type_alias() is None
    assert p.type_aliases["Age"] == "int"

    p = parser([
        Token("KEYWORD", "type", 1, 1), Token("IDENTIFIER", "int", 1, 6), Token("OPERATOR", "=", 1, 10), Token("DATATYPE", "int", 1, 12), Token("PUNCTUATION", ";", 1, 15),
    ])
    with pytest.raises(SyntaxError, match="Cannot redefine built-in type 'int'"):
        p.parse_type_alias()

    p = parser([
        Token("KEYWORD", "watch", 1, 1), Token("IDENTIFIER", "a", 1, 7), Token("PUNCTUATION", ",", 1, 8), Token("IDENTIFIER", "b", 1, 10), Token("PUNCTUATION", ";", 1, 11),
    ])
    assert p.parse_watch_statement()["variables"] == ["a", "b"]

    p = parser([
        Token("KEYWORD", "use", 1, 1), Token("KEYWORD", "mut", 1, 5), Token("IDENTIFIER", "a", 1, 9), Token("PUNCTUATION", ",", 1, 10), Token("IDENTIFIER", "b", 1, 12), Token("PUNCTUATION", ";", 1, 13),
    ])
    use_stmt = p.parse_use_statement()
    assert use_stmt["is_mutable"] is True
    assert use_stmt["variables"] == ["a", "b"]