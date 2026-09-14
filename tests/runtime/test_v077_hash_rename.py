from echo.formatter import format_source
from echo.frontend.ast.nodes import DestructureDeclaration, HashPattern, NamePattern
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_hash_rename():
    statement = parse_source("{ id as userId: int, name: str } = user;").statements[0]
    assert isinstance(statement, DestructureDeclaration)
    assert isinstance(statement.pattern, HashPattern)
    first, second = statement.pattern.fields
    assert isinstance(first, NamePattern)
    assert first.key == "id"
    assert first.name == "userId"
    assert second.key is None
    assert second.name == "name"


def test_hash_rename_binds_local_name():
    result = run_echo(
        """
user: hash = { id: 7, name: "Ada" };
{ id as userId: int, name: str } = user;
say(userId);
say(name);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["7", "Ada"]


def test_hash_rename_assignment_omits_types():
    result = run_echo(
        """
user: hash = { id: 3 };
userId: int = 0;
{ id as userId } = user;
say(userId);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "3"


def test_hash_rename_missing_key_is_e2711():
    result = run_echo('{ id as userId: int } = { name: "x" };')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2711" in result.output
    assert "id" in result.output


def test_hash_rename_in_fn_param():
    result = run_echo(
        """
fn label({ id as userId: int }) -> int {
    return userId;
}
say(label({ id: 11 }));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "11"


def test_hash_rename_in_switch_arm():
    result = run_echo(
        """
user: hash = { id: 5 };
switch user {
    { id as userId: int } { say(userId); }
    else { say("no"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "5"


def test_same_name_as_is_plain_binding():
    statement = parse_source("{ id as id: int } = user;").statements[0]
    field = statement.pattern.fields[0]
    assert field.key is None
    assert field.name == "id"


def test_formatter_prints_hash_rename():
    assert (
        format_source("{id as userId:int,name:str}=user;")
        == "{id as userId: int, name: str} = user;\n"
    )
    formatted = format_source("{ id as userId: int } = user;")
    assert format_source(formatted) == formatted


def test_as_is_a_keyword_not_an_identifier():
    result = run_echo("as: int = 1;")
    assert result.exit_code == 1
    assert_no_python_leak(result)
