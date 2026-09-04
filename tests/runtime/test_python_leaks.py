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
