from helpers import run_echo


def test_for_expression_bounds_and_negative_start():
    result = run_echo(
        """
        n: int = 2;
for i: int in -1..n {
    say(i);
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["-1", "0", "1", "2"]


def test_for_by_zero_is_an_error():
    result = run_echo("for i: int in 0..3 by 0 { say(i); }\n")
    assert result.exit_code == 1
    assert "by 0" in result.output


def test_compound_assignment():
    result = run_echo("x: int = 1;\nx += 2;\nsay(x);\n")
    assert result.exit_code == 0
    assert result.output.strip() == "3"
