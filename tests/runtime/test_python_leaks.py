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


def test_foreach_hash_insert_does_not_leak_python():
    result = run_echo(
        """
h: hash = { a: 1 };
foreach k: str in h {
    h["b"] = 2;
    say(k);
}
say(h["b"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ["a", "2"]


def test_foreach_hash_take_does_not_leak_python():
    result = run_echo(
        """
h: hash = { a: 1, b: 2 };
foreach k: str in h {
    h.take(k);
    say(k);
}
say(length(h));
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert set(result.lines[:2]) == {"a", "b"}
    assert result.lines[-1] == "0"


def test_foreach_list_push_does_not_hang_or_leak_python():
    result = run_echo(
        """
xs: list = [1, 2];
foreach x: int in xs {
    xs.push(x);
    say(x);
}
say(length(xs));
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ["1", "2", "4"]


def test_foreach_list_insert_at_front_does_not_hang_or_leak_python():
    result = run_echo(
        """
xs: list = [1, 2];
foreach x: int in xs {
    xs.insertAt(0, 99);
    say(x);
}
say(xs.asString());
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ["1", "2", "[99, 99, 1, 2]"]


def test_map_values_insert_does_not_leak_python():
    result = run_echo(
        """
h: hash = { a: 1 };
fn grow(v: int) -> int {
    use mut h;
    h["b"] = 2;
    return v + 1;
}
say(h.mapValues(grow));
say(h["b"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ['{"a": 2}', "2"]


def test_filter_hash_insert_does_not_leak_python():
    result = run_echo(
        """
h: hash = { a: 1 };
fn keep(v: int) -> bool {
    use mut h;
    h["b"] = 2;
    return true;
}
say(h.filter(keep));
say(h["b"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ['{"a": 1}', "2"]


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
