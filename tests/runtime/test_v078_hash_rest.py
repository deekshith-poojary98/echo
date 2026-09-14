from echo.formatter import format_source
from echo.frontend.ast.nodes import DestructureDeclaration, HashPattern, NamePattern
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.errors import ParseError
from helpers import assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_hash_rest():
    statement = parse_source("{ id: int, rest: dynamic... } = user;").statements[0]
    assert isinstance(statement, DestructureDeclaration)
    assert isinstance(statement.pattern, HashPattern)
    rest = statement.pattern.fields[-1]
    assert isinstance(rest, NamePattern)
    assert rest.rest
    assert rest.rest_container == "hash"
    assert rest.name == "rest"


def test_hash_rest_binds_leftover_keys():
    result = run_echo(
        """
user: hash = { id: 7, name: "Ada", role: "admin" };
{ id: int, rest: dynamic... } = user;
say(id);
say(rest["name"]);
say(rest["role"]);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["7", "Ada", "admin"]


def test_hash_rest_empty_when_no_extras():
    result = run_echo(
        """
user: hash = { id: 1 };
{ id: int, rest: dynamic... } = user;
say(rest == {});
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "true"


def test_hash_rest_value_type_checked():
    result = run_echo(
        """
user: hash = { id: 1, name: "x" };
{ id: int, rest: int... } = user;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output or "int" in result.output


def test_hash_rest_must_be_last():
    try:
        parse_source("{ rest: dynamic..., id: int } = user;")
        assert False, "expected ParseError"
    except ParseError as exc:
        assert "last" in str(exc).lower()


def test_hash_rest_forbids_as_rename():
    try:
        parse_source("{ id as extras: dynamic... } = user;")
        assert False, "expected ParseError"
    except ParseError as exc:
        assert "as" in str(exc).lower() or "rest" in str(exc).lower()


def test_hash_rest_assignment_omits_types():
    result = run_echo(
        """
user: hash = { id: 2, nick: "a" };
id: int = 0;
rest: hash = {};
{ id, rest... } = user;
say(id);
say(rest["nick"]);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["2", "a"]


def test_hash_rest_with_rename_fixed_field():
    result = run_echo(
        """
user: hash = { id: 9, city: "Goa" };
{ id as userId: int, rest: dynamic... } = user;
say(userId);
say(rest["city"]);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["9", "Goa"]


def test_hash_rest_in_switch_arm():
    result = run_echo(
        """
user: hash = { id: 3, tag: "ok" };
switch user {
    { id: int, rest: dynamic... } { say(id); say(rest["tag"]); }
    else { say("no"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "ok"]


def test_formatter_prints_hash_rest():
    assert (
        format_source("{id:int,rest:dynamic...}=user;")
        == "{id: int, rest: dynamic...} = user;\n"
    )
    formatted = format_source("{ id: int, rest: dynamic... } = user;")
    assert format_source(formatted) == formatted
