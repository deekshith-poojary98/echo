from helpers import assert_no_python_leak, run_echo


def test_if_type_narrows_union_in_then():
    result = run_echo(
        """
wide: int | str = 1;
if (type(wide) == "int") {
    n: int = wide;
    say(n);
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_reversed_type_equality_also_narrows():
    result = run_echo(
        """
wide: int | str = 7;
if ("int" == type(wide)) {
    n: int = wide;
    say(n);
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "7"


def test_else_if_type_narrows():
    result = run_echo(
        """
wide: int | str = "hi";
if (type(wide) == "int") {
    n: int = wide;
    say(n);
} else if (type(wide) == "str") {
    s: str = wide;
    say(s);
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "hi"


def test_else_excludes_guarded_member():
    result = run_echo(
        """
wide: int | str | bool = true;
if (type(wide) == "int") {
    n: int = wide;
    say(n);
} else {
    rest: str | bool = wide;
    say(rest);
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "true"


def test_else_rejects_excluded_member_assign():
    result = run_echo(
        """
wide: int | str = "x";
if (type(wide) == "int") {
    say(wide);
} else {
    n: int = wide;
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_union_not_assignable_to_member_without_guard():
    result = run_echo(
        """
wide: int | str = "x";
n: int = wide;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output
    assert "int | str" in result.output


def test_class_name_narrowing():
    result = run_echo(
        """
class Point {
    new { x: int; y: int; }
}
p: Point | str = Point(1, 2);
if (type(p) == "Point") {
    q: Point = p;
    say(q.x);
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_dynamic_still_skips_static_union_assign():
    from echo.frontend.lexer import Lexer
    from echo.frontend.parser import Parser
    from echo.semantics.analyzer import SemanticAnalyzer

    program = Parser(
        Lexer().tokenize(
            """
wide: dynamic = "x";
n: int = wide;
"""
        )
    ).parse()
    SemanticAnalyzer().analyze(program)
