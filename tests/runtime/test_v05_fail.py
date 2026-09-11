from helpers import assert_no_python_leak, run_echo


def test_fail_aborts_with_message():
    result = run_echo('fail("boom");\nsay("nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "boom" in result.output
    assert "E2825" in result.output
    assert "AssertionError" not in result.output
    assert "nope" not in result.output


def test_fail_message_must_be_string():
    result = run_echo("fail(1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "message must be a string" in result.output
    assert "E2825" in result.output


def test_fail_requires_a_message():
    result = run_echo("fail();\n")
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "at least 1" in result.output


def test_fail_keyword_argument():
    result = run_echo('fail(message: "from keyword");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "from keyword" in result.output
    assert "E2825" in result.output


def test_fail_method_form():
    result = run_echo('"from method".fail();\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "from method" in result.output
    assert "E2825" in result.output
