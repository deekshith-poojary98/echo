from helpers import assert_no_python_leak, run_echo


def test_int_division_truncates_toward_zero():
    result = run_echo("say(7 / 2);\nsay(-7 / 2);\n")
    assert result.exit_code == 0
    assert result.lines == ["3", "-3"]


def test_mixed_division_is_float():
    result = run_echo("say(7 / 2.0);\n")
    assert result.exit_code == 0
    assert result.output.strip().startswith("3.5")


def test_int_modulo_uses_toward_zero_quotient():
    result = run_echo("say(7 % 2);\nsay(-7 % 2);\n")
    assert result.exit_code == 0
    assert result.lines == ["1", "-1"]


def test_division_by_zero_is_echo_runtime_error():
    result = run_echo("say(1 / 0);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "division by zero" in result.output.lower()


def test_modulo_by_zero_is_echo_runtime_error():
    result = run_echo("say(1 % 0);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "modulo by zero" in result.output.lower()


def test_string_concatenation():
    result = run_echo('say("a" + "b");\n')
    assert result.exit_code == 0
    assert result.output.strip() == "ab"


def test_list_concatenation():
    result = run_echo("say([1] + [2]);\n")
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2]"


def test_unary_minus_rejects_bool():
    result = run_echo("say(-true);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_comparison_rejects_mixed_types():
    result = run_echo('say(1 < "a");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot compare" in result.output


def test_and_or_short_circuit():
    result = run_echo(
        """
fn boom() -> bool {
    say("BOOM");
    return true;
}
say(false && boom());
say(true || boom());
"""
    )
    assert result.exit_code == 0
    assert "BOOM" not in result.output
    assert result.lines == ["false", "true"]


def test_arguments_evaluate_left_to_right():
    result = run_echo(
        """
fn show(a: int, b: int) {
    say(a, b);
}
fn one() -> int { say("L"); return 1; }
fn two() -> int { say("R"); return 2; }
show(one(), two());
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["L", "R", "1 2"]


def test_compound_assignment_is_add_then_assign():
    result = run_echo(
        """
x: int = 10;
x -= 3;
x *= 2;
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "14"
