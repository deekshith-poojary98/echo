from helpers import run_echo


def test_unknown_name_is_echo_error():
    result = run_echo("say(unknown);")
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "unknown" in result.output


def test_index_out_of_range_is_echo_error():
    result = run_echo("x: list = [1, 2];\nx[99];\n")
    assert result.exit_code == 1
    assert "Index Error" in result.output
    assert "99" in result.output
    assert "IndexError:" not in result.output


def test_string_plus_int_is_echo_type_error():
    result = run_echo('x: str = "hello";\nx += 2;\n')
    assert result.exit_code == 1
    assert "Type Error" in result.output
    assert "Cannot add str and int" in result.output
    assert "TypeError:" not in result.output or "Error[E2101]" in result.output


def test_mixed_comparison_is_echo_type_error():
    result = run_echo('say(1 < "a");')
    assert result.exit_code == 1
    assert "Cannot compare" in result.output
    assert "not supported between instances" not in result.output


def test_asint_invalid_is_echo_error():
    result = run_echo('say("abc".asInt());')
    assert result.exit_code == 1
    assert "Cannot convert value to int" in result.output
    assert "invalid literal" not in result.output


def test_wait_without_args_is_echo_error():
    result = run_echo("wait();")
    assert result.exit_code == 1
    assert "wait() requires a seconds argument" in result.output
    assert "list index out of range" not in result.output
