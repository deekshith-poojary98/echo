from helpers import assert_no_python_leak, run_echo


def test_assert_passes_on_truthy():
    result = run_echo(
        """
assert(true, "nope");
assert(1, "nope");
assert("ok", "nope");
say("yes");
"""
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "yes"


def test_assert_aborts_on_falsy_with_message():
    result = run_echo('assert(false, "boom");\nsay("nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "boom" in result.output
    assert "AssertionError" not in result.output
    assert "nope" not in result.output


def test_assert_treats_zero_empty_and_null_as_falsy():
    result = run_echo("assert(0, \"zero\");\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "zero" in result.output

    result = run_echo('assert("", "empty");\n')
    assert result.exit_code == 1
    assert "empty" in result.output

    result = run_echo("assert(null, \"missing\");\n")
    assert result.exit_code == 1
    assert "missing" in result.output


def test_assert_message_must_be_string():
    result = run_echo("assert(false, 1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "message must be a string" in result.output


def test_assert_requires_two_standalone_args():
    result = run_echo("assert(true);\n")
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "at least 2" in result.output


def test_assert_method_form():
    result = run_echo('false.assert("from method");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "from method" in result.output
