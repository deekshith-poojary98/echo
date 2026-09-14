from echo.formatter import format_source
from echo.frontend.ast.nodes import LiteralPattern, SwitchStatement, TypePattern
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_literal_and_else_arms():
    statement = parse_source(
        """
switch x {
    0 { say("zero"); }
    else { say("other"); }
}
"""
    ).statements[0]
    assert isinstance(statement, SwitchStatement)
    assert len(statement.arms) == 2
    assert isinstance(statement.arms[0].pattern, LiteralPattern)
    assert statement.arms[0].pattern.value == 0
    assert statement.arms[1].pattern is None


def test_parser_builds_type_pattern_with_binding():
    statement = parse_source(
        """
switch x {
    int n { say(n); }
    else { say("other"); }
}
"""
    ).statements[0]
    assert isinstance(statement, SwitchStatement)
    pattern = statement.arms[0].pattern
    assert isinstance(pattern, TypePattern)
    assert pattern.binding == "n"


def test_literal_switch_with_else():
    result = run_echo(
        """
x: int = 1;
switch x {
    0 { say("zero"); }
    1 { say("one"); }
    else { say("other"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "one"


def test_else_arm_runs_when_no_literal_matches():
    result = run_echo(
        """
x: int = 9;
switch x {
    0 { say("zero"); }
    1 { say("one"); }
    else { say("other"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "other"


def test_missing_else_is_e3210():
    result = run_echo(
        """
x: int = 1;
switch x {
    0 { say("zero"); }
    1 { say("one"); }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3210" in result.output


def test_bool_true_false_is_exhaustive():
    result = run_echo(
        """
flag: bool = false;
switch flag {
    true { say("yes"); }
    false { say("no"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "no"


def test_union_type_arms_are_exhaustive():
    result = run_echo(
        """
id: int | str = "x";
switch id {
    int n { say(n); }
    str s { say(s); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "x"


def test_union_type_arms_bind_and_dispatch():
    result = run_echo(
        """
id: int | str = 7;
switch id {
    int n { say(n); }
    str s { say(s); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "7"


def test_partial_union_coverage_needs_else():
    result = run_echo(
        """
id: int | str = 1;
switch id {
    int n { say(n); }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3210" in result.output


def test_failed_destructure_falls_through():
    result = run_echo(
        """
pair: list = [1];
switch pair {
    [a: int, b: int] { say("pair"); }
    else { say("short"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "short"


def test_list_destructure_arm_binds():
    result = run_echo(
        """
pair: list = [3, 4];
switch pair {
    [a: int, b: int] { say(a); say(b); }
    else { say("no"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "4"]


def test_hash_destructure_arm_binds():
    result = run_echo(
        """
user: hash = { id: 9, name: "Ada" };
switch user {
    { id: int, name: str } { say(id); say(name); }
    else { say("no"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["9", "Ada"]


def test_abort_inside_arm_still_aborts():
    result = run_echo(
        """
x: int = 1;
switch x {
    1 { fail("boom"); }
    else { say("other"); }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "boom" in result.output


def test_formatter_prints_switch():
    formatted = format_source(
        """
switch x{0{say("z");}else{say("o");}}
"""
    )
    assert "switch x {" in formatted
    assert "0 {" in formatted
    assert "else {" in formatted
    assert format_source(formatted) == formatted
