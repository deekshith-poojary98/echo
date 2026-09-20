from helpers import assert_no_python_leak, run_echo


def test_foreach_over_int_is_echo_error_not_python():
    result = run_echo(
        """
foreach item: int in 1 {
    say(item);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "foreach" in result.output.lower() or "Type Error" in result.output or "Execution Error" in result.output


def test_foreach_over_null_is_echo_error_not_python():
    result = run_echo(
        """
xs: dynamic = null;
foreach item: dynamic in xs {
    say(item);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_order_mixed_types_is_echo_error_not_python():
    result = run_echo(
        """
xs: list = [1, "a"];
xs.order();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_out_of_range_index_assignment_is_echo_error():
    result = run_echo(
        """
xs: list = [1];
xs[9] = 2;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "out of range" in result.output.lower() or "Index" in result.output or "Execution Error" in result.output


def test_missing_hash_key_assignment_is_echo_error():
    result = run_echo(
        """
h: hash = {"a": {"b": 1}};
h["missing"]["b"] = 2;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_as_int_invalid_does_not_mention_python_literal():
    result = run_echo('say("abc".asInt());\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_wait_non_numeric_is_echo_error():
    result = run_echo('wait("nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output


def test_wait_negative_is_echo_error_not_python():
    result = run_echo("wait(-1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "non-negative" in result.output


def test_wait_nonfinite_is_echo_error_not_python():
    result = run_echo("wait(1e400);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output

    result = run_echo("wait(1e400 - 1e400);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output


def test_wait_integer_too_large_for_float_is_echo_error_not_python():
    huge = "1" + "0" * 400
    result = run_echo(f"wait({huge});\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output


def test_as_int_infinity_is_echo_error_not_python():
    result = run_echo("say(asInt(1e400));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_as_int_or_infinity_returns_fallback():
    result = run_echo("say(asIntOr(1e400, 0));\n")
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "0"


def test_as_int_overflowed_multiply_is_echo_error_not_python():
    result = run_echo(
        """
x: float = 1e308;
say(asInt(x * 10));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_floor_ceil_infinity_is_echo_error_not_python():
    result = run_echo("say(floor(1e400));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "finite" in result.output.lower() or "floor()" in result.output

    result = run_echo("say(ceil(1e400));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "finite" in result.output.lower() or "ceil()" in result.output


def test_for_and_range_infinity_is_echo_error_not_python():
    result = run_echo(
        """
for i: int in 0...1e400 {
    say(i);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "convertible to int" in result.output

    result = run_echo("say(0...1e400);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "convertible to int" in result.output


def test_for_bool_bound_is_echo_error_not_python_int_true():
    result = run_echo(
        """
for i: int in true..3 {
    say(i);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_remove_missing_value_is_echo_error():
    result = run_echo(
        """
xs: list = [1];
xs.removeValue(9);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not found" in result.output.lower()


def test_hash_take_missing_key_is_echo_error():
    result = run_echo(
        """
h: hash = {};
h.take("nope");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
