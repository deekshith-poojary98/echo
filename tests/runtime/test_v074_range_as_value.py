from echo.errors import SemanticError
from echo.formatter import format_source
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.semantics.analyzer import SemanticAnalyzer
from helpers import run_echo


def test_exclusive_range_expression():
    result = run_echo("say(0...5);\n")
    assert result.exit_code == 0
    assert result.output.strip() == "[0, 1, 2, 3, 4]"


def test_inclusive_range_expression():
    result = run_echo("say(0..5);\n")
    assert result.exit_code == 0
    assert result.output.strip() == "[0, 1, 2, 3, 4, 5]"


def test_empty_exclusive_and_inclusive():
    result = run_echo(
        """
say(0...0);
say(0..0);
say(5...3);
say(5..3);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[]", "[0]", "[]", "[]"]


def test_range_by_step():
    result = run_echo(
        """
say(0...10 by 2);
say(0..10 by 2);
say(10...0 by -2);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[0, 2, 4, 6, 8]", "[0, 2, 4, 6, 8, 10]", "[10, 8, 6, 4, 2]"]


def test_assign_to_list_and_map():
    result = run_echo(
        """
xs: list = 0...5;
ys: list = 0..5;
zs: list = 0...10 by 2;
say(xs);
say(ys);
say(zs);
say(xs.map(fn(n: int) -> int { return n * 2; }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == [
        "[0, 1, 2, 3, 4]",
        "[0, 1, 2, 3, 4, 5]",
        "[0, 2, 4, 6, 8]",
        "[0, 2, 4, 6, 8]",
    ]


def test_pass_range_to_map_directly():
    result = run_echo('say(map(0...4, fn(n: int) -> int { return n + 1; }));\n')
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2, 3, 4]"


def test_foreach_over_range_allocates_list():
    result = run_echo(
        """
foreach i: int in 0...3 {
    say(i);
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["0", "1", "2"]


def test_for_loop_still_iterates_without_range_value():
    result = run_echo(
        """
for i: int in 0...5 by 2 {
    say(i);
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["0", "2", "4"]


def test_range_matches_range_list_builtins():
    result = run_echo(
        """
say(0...5 == rangeList(0, 5));
say(0..5 == rangeListInclusive(0, 5));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["true", "true"]


def test_range_by_zero_is_an_error():
    result = run_echo("say(0...5 by 0);\n")
    assert result.exit_code == 1
    assert "by 0" in result.output


def test_non_int_bounds_are_type_errors():
    result = run_echo("xs: list = true...5;\n")
    assert result.exit_code == 1
    assert "convertible to int" in result.output

    result = run_echo('ys: list = 0..."z";\n')
    assert result.exit_code == 1
    assert "convertible to int" in result.output


def test_analyzer_rejects_literal_non_int_bounds():
    source = "xs: list = true...5;\n"
    tokens = Lexer().tokenize(source)
    program = Parser(tokens).parse()
    try:
        SemanticAnalyzer().analyze(program)
        assert False, "expected SemanticError"
    except SemanticError as exc:
        assert exc.code == "E1015"
        assert "convertible to int" in exc.message


def test_formatter_prints_range_expressions():
    assert format_source("xs:list=0...5;") == "xs: list = 0...5;\n"
    assert format_source("xs:list=0..5;") == "xs: list = 0..5;\n"
    assert format_source("xs:list=0...10 by 2;") == "xs: list = 0...10 by 2;\n"
    assert format_source("xs:list=0...10 by 1;") == "xs: list = 0...10;\n"


def test_list_element_and_argument_forms():
    result = run_echo(
        """
items: list = [0...3, 0..2];
say(items);
say(length(0...4));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[0, 1, 2], [0, 1, 2]]", "4"]
