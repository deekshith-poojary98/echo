from helpers import run_echo


def test_declaration_and_assignment():
    result = run_echo('count: int = 1;\ncount = 2;\nsay(count);\n')
    assert result.exit_code == 0
    assert result.output.strip() == "2"


def test_null_does_not_leak_to_parent():
    result = run_echo(
        """
x: dynamic = 1;
if true {
  x: dynamic = null;
  say(x);
}
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["null", "1"]


def test_bool_is_not_an_int():
    result = run_echo("x: int = true;\n")
    assert result.exit_code == 1
    assert "Type Error" in result.output


def test_undeclared_assignment():
    result = run_echo("count = 1;\n")
    assert result.exit_code == 1
    assert "not declared" in result.output


def test_redeclare_same_name_in_same_scope_is_an_error():
    result = run_echo("x: int = 1;\nx: int = 2;\n")
    assert result.exit_code == 1
    assert "already" in result.output.lower() or "redefin" in result.output.lower() or "declared" in result.output.lower()
