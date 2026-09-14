from echo.formatter import format_source
from echo.frontend.ast.nodes import TypeAliasStatement, TypeName, UnionType, VariableDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.runtime.values import matches_type, type_assignable
from helpers import assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_flat_union_types():
    declaration = parse_source("id: int | str = 1;").statements[0]
    assert isinstance(declaration, VariableDeclaration)
    assert isinstance(declaration.declared_type, UnionType)
    names = [m.name for m in declaration.declared_type.members if isinstance(m, TypeName)]
    assert names == ["int", "str"]


def test_parser_allows_spaces_optional_around_pipe():
    tight = parse_source("x:int|str=1;").statements[0]
    spaced = parse_source("x: int | str = 1;").statements[0]
    assert isinstance(tight.declared_type, UnionType)
    assert isinstance(spaced.declared_type, UnionType)


def test_int_or_str_accepts_both_branches():
    result = run_echo(
        """
id: int | str = 1;
say(id);
id = "x";
say(id);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["1", "x"]


def test_bool_rejected_from_int_or_str():
    result = run_echo("id: int | str = true;")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output
    assert "int | str" in result.output


def test_reassignment_rejects_non_member():
    result = run_echo(
        """
id: int | str = 1;
id = false;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_type_alias_union():
    result = run_echo(
        """
type Id = int | str;
id: Id = 1;
id = "x";
say(id);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "x"


def test_nested_and_aliased_unions_flatten():
    program = parse_source(
        """
type Id = int | str;
type Wide = Id | bool | int;
x: Wide = true;
"""
    )
    from echo.semantics.analyzer import SemanticAnalyzer

    analyzer = SemanticAnalyzer()
    analyzer.analyze(program)
    declaration = program.statements[-1]
    assert isinstance(declaration, VariableDeclaration)
    assert isinstance(declaration.declared_type, UnionType)
    names = sorted(
        m.name for m in declaration.declared_type.members if isinstance(m, TypeName)
    )
    assert names == ["bool", "int", "str"]


def test_fn_param_union():
    result = run_echo(
        """
fn show(x: int | str) -> str {
    return asString(x);
}
say(show(1));
say(show("hi"));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["1", "hi"]


def test_fn_param_union_rejects_bool():
    result = run_echo(
        """
fn show(x: int | str) -> str {
    return asString(x);
}
show(true);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2706" in result.output or "E2001" in result.output
    assert "int | str" in result.output


def test_list_or_hash_union():
    result = run_echo(
        """
box: list | hash = [1, 2];
say(length(box));
box = { "a": 1 };
say(box["a"]);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["2", "1"]


def test_exact_in_union():
    result = run_echo(
        """
value: exact { id: int } | str = { id: 1 };
say(value["id"]);
value = "ok";
say(value);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["1", "ok"]


def test_exact_in_union_rejects_extra_via_no_branch():
    result = run_echo('value: exact { id: int } | str = { id: 1, name: "x" };')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_null_is_not_a_union_member_type():
    result = run_echo("x: str | null = null;")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Expected type" in result.output or "Parse" in result.output


def test_void_may_be_a_union_member_for_null():
    result = run_echo(
        """
x: str | void = null;
say(x);
x = "hi";
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["null", "hi"]


def test_union_not_assignable_to_narrower_member_when_value_mismatches():
    result = run_echo(
        """
wide: int | str = "x";
narrow: int = wide;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_member_assignable_to_union_statically():
    from echo.errors import SourceLocation

    loc = SourceLocation(1, 1)
    int_t = TypeName(loc, "int")
    str_t = TypeName(loc, "str")
    union = UnionType(loc, [int_t, str_t])
    assert type_assignable(int_t, union)
    assert not type_assignable(union, int_t)
    assert type_assignable(union, union)


def test_matches_type_any_branch():
    union = parse_source("x: int | str = 1;").statements[0].declared_type
    assert matches_type(1, union)
    assert matches_type("a", union)
    assert not matches_type(True, union)


def test_formatter_prints_union_with_spaces():
    assert format_source("x:int|str=1;") == "x: int | str = 1;\n"
    assert format_source("type Id=int|str;") == "type Id = int | str;\n"
    once = format_source("fn show(x:int|str)->str{return asString(x);}")
    assert "int | str" in once
    assert format_source(once) == once


def test_fn_return_union():
    result = run_echo(
        """
fn pick(flag: bool) -> int | str {
    if (flag) {
        return 1;
    }
    return "x";
}
say(pick(true));
say(pick(false));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["1", "x"]


def test_duplicate_members_flatten_at_resolve():
    result = run_echo(
        """
type Id = int | str | int;
id: Id = "ok";
say(id);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "ok"
    program = parse_source("type Id = int | str | int;\nid: Id = 1;")
    from echo.semantics.analyzer import SemanticAnalyzer

    SemanticAnalyzer().analyze(program)
    alias = program.statements[0]
    assert isinstance(alias, TypeAliasStatement)
    assert isinstance(alias.target, UnionType)
    assert len(alias.target.members) == 2
