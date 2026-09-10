from helpers import assert_no_python_leak, run_echo


def test_now_returns_int_unix_seconds():
    result = run_echo(
        """
t: int = now();
say(t.type());
say(t >= 0);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["int", "true"]


def test_now_rejects_arguments():
    result = run_echo("say(now(1));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "takes no arguments" in result.output


def test_random_is_float_in_unit_interval():
    result = run_echo(
        """
x: float = random();
say(x.type());
say(x >= 0);
say(x < 1);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["float", "true", "true"]


def test_random_rejects_arguments():
    result = run_echo("say(random(1));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "takes no arguments" in result.output


def test_random_int_inclusive_and_equal_bounds():
    result = run_echo(
        """
say(randomInt(4, 4));
n: int = randomInt(2, 5);
say(n >= 2);
say(n <= 5);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["4", "true", "true"]


def test_random_int_rejects_bool():
    result = run_echo("say(randomInt(true, 3));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "integer" in result.output


def test_random_int_rejects_min_greater_than_max():
    result = run_echo("say(randomInt(5, 1));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "min must be <= max" in result.output
