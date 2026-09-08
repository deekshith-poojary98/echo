from helpers import assert_no_python_leak, run_echo


def test_asint_parses_trimmed_integer_text():
    result = run_echo('say(" 42 ".asInt());\nsay(asInt("-7"));\n')
    assert result.exit_code == 0, result.output
    assert result.lines == ["42", "-7"]


def test_asint_truncates_float_toward_zero():
    result = run_echo("say(asInt(3.9));\nsay(asInt(-3.9));\n")
    assert result.exit_code == 0, result.output
    assert result.lines == ["3", "-3"]


def test_asint_rejects_bool():
    result = run_echo("say(asInt(true));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert bool to int" in result.output


def test_asint_rejects_false():
    result = run_echo("say(false.asInt());\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert bool to int" in result.output


def test_asint_rejects_decimal_string():
    result = run_echo('say("3.9".asInt());\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_asint_rejects_null_and_list():
    result = run_echo("say(asInt(null));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_asfloat_rejects_bool():
    result = run_echo("say(asFloat(true));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert bool to float" in result.output


def test_asfloat_accepts_int_and_string():
    result = run_echo('say(asFloat(7));\nsay("3.5".asFloat());\n')
    assert result.exit_code == 0, result.output
    assert result.lines == ["7.0", "3.5"]


def test_asbool_keeps_truthiness():
    result = run_echo(
        """
say(asBool(0));
say(asBool(""));
say(asBool([]));
say(asBool("hi"));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["false", "false", "false", "true"]
