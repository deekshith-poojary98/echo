from helpers import assert_no_python_leak, run_echo


def test_abs_int_and_float():
    result = run_echo(
        """
n: int = -3;
say(n.abs());
say(abs(-3.5));
say(abs(2));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["3", "3.5", "2"]


def test_abs_rejects_bool():
    result = run_echo("say(abs(true));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "requires a number" in result.output


def test_min_max_two_numbers():
    result = run_echo(
        """
say(min(2, 5));
say(max(2, 5));
say(min(1.5, 1));
say(max(-3, -1));
say(2.min(9));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["2", "5", "1", "-1", "2"]


def test_min_rejects_bool():
    result = run_echo("say(min(true, 1));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "requires a number" in result.output


def test_max_rejects_string():
    result = run_echo('say(max(1, "a"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "requires a number" in result.output


def test_floor_and_ceil():
    result = run_echo(
        """
say(floor(3.2));
say(ceil(3.2));
say(floor(-3.2));
say(ceil(-3.2));
say(floor(4));
say(ceil(4));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["3", "4", "-4", "-3", "4", "4"]


def test_floor_rejects_bool():
    result = run_echo("say(floor(false));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "requires a number" in result.output
