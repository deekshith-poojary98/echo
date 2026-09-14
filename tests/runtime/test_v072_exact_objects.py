from echo.formatter import format_source
from echo.frontend.ast.nodes import ObjectType, TypeAliasStatement, VariableDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.runtime.values import matches_type
from helpers import assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_marks_inline_and_aliased_exact_types():
    program = parse_source(
        "type User = exact { id: int, name: str };"
        'user: exact { id: int } = { id: 1 };'
    )
    alias = program.statements[0]
    declaration = program.statements[1]
    assert isinstance(alias, TypeAliasStatement)
    assert isinstance(alias.target, ObjectType)
    assert alias.target.exact
    assert isinstance(declaration, VariableDeclaration)
    assert isinstance(declaration.declared_type, ObjectType)
    assert declaration.declared_type.exact


def test_exact_alias_accepts_its_declared_shape():
    result = run_echo(
        """
type User = exact { id: int, name: str };
user: User = { id: 1, name: "Ada" };
say(user["name"]);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_open_object_still_allows_extra_fields():
    result = run_echo(
        """
type User = { id: int };
user: User = { id: 1, name: "Ada" };
say(user["name"]);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_exact_declaration_rejects_extra_field_with_e3208():
    result = run_echo('user: exact { id: int } = { id: 1, name: "Ada" };')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3208" in result.output


def test_exact_declaration_rejects_missing_field_with_e3209():
    result = run_echo("user: exact { id: int, name: str } = { id: 1 };")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3209" in result.output


def test_exact_declaration_rejects_wrong_field_type():
    result = run_echo('user: exact { id: int } = { id: "one" };')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_exact_to_compatible_open_assignment_is_allowed():
    result = run_echo(
        """
exactUser: exact { id: int, name: str } = { id: 1, name: "Ada" };
openUser: { id: int } = exactUser;
say(openUser["name"]);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_open_to_exact_assignment_is_rejected():
    result = run_echo(
        """
openUser: { id: int } = { id: 1 };
exactUser: exact { id: int } = openUser;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_reassignment_checks_open_to_exact_direction():
    result = run_echo(
        """
target: exact { id: int } = { id: 1 };
source: { id: int } = { id: 2 };
target = source;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_destructured_exact_field_accepts_exact_source_field():
    result = run_echo(
        """
source: { user: exact { id: int } } = { user: { id: 1 } };
{ user: exact { id: int } } = source;
say(user["id"]);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_destructured_exact_field_rejects_open_source_field():
    result = run_echo(
        """
source: { user: { id: int } } = { user: { id: 1 } };
{ user: exact { id: int } } = source;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_exact_argument_rejects_extra_field():
    result = run_echo(
        """
fn id(user: exact { id: int }) -> int { return user["id"]; }
id({ id: 1, extra: true });
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3208" in result.output


def test_exact_return_rejects_extra_field():
    result = run_echo(
        """
fn user() -> exact { id: int } {
    return { id: 1, extra: true };
}
user();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3208" in result.output


def test_open_typed_value_cannot_be_returned_as_exact():
    result = run_echo(
        """
fn user() -> exact { id: int } {
    value: { id: int } = { id: 1 };
    return value;
}
user();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_exact_typed_value_can_be_returned_as_open():
    result = run_echo(
        """
fn user() -> { id: int } {
    value: exact { id: int, name: str } = { id: 1, name: "Ada" };
    return value;
}
say(user()["name"]);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_exact_foreach_binding_rejects_extra_field():
    result = run_echo(
        """
items: list = [{ id: 1, extra: true }];
foreach item: exact { id: int } in items {
    say(item["id"]);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3208" in result.output


def test_nested_exact_rejects_extra_field():
    result = run_echo(
        """
record: { user: exact { id: int } } = {
    user: { id: 1, extra: true }
};
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3208" in result.output


def test_exact_is_not_frozen():
    result = run_echo(
        """
user: exact { id: int } = { id: 1 };
user["id"] = 2;
say(user["id"]);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "2"


def test_matches_type_enforces_exact_shape():
    annotation = parse_source("x: exact { id: int } = { id: 1 };").statements[0].declared_type
    assert matches_type({"id": 1}, annotation)
    assert not matches_type({}, annotation)
    assert not matches_type({"id": 1, "extra": True}, annotation)
    assert not matches_type({"id": "one"}, annotation)


def test_formatter_preserves_exact_types():
    source = "type User=exact{id:int,name:exact{first:str}};user:User={id:1,name:{first:'Ada'}};"
    expected = (
        "type User = exact {id: int, name: exact {first: str}};\n"
        'user: User = {id: 1, name: {first: "Ada"}};\n'
    )
    assert format_source(source) == expected
    assert format_source(expected) == expected
