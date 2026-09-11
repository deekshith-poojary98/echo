from helpers import assert_no_python_leak, run_echo


def test_expect_outside_echo_test_aborts_like_assert():
    result = run_echo('expect(false, "boom");\nsay("after");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "boom" in result.output
    assert "E2826" in result.output
    assert "after" not in result.output


def test_expect_outside_echo_test_passes():
    result = run_echo('expect(true, "ok");\nsay("yes");\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "yes"


def test_expect_condition_must_be_bool():
    result = run_echo('expect(1, "nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "condition must be a bool" in result.output
    assert "E2826" in result.output


def test_expect_message_must_be_string():
    result = run_echo("expect(true, 1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "message must be a string" in result.output


def test_expect_requires_two_standalone_args():
    result = run_echo("expect(true);\n")
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "at least 2" in result.output


def test_expect_eq_outside_echo_test_aborts_on_mismatch():
    result = run_echo('expectEq(1, 2, "mismatch");\nsay("after");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "mismatch" in result.output
    assert "E2827" in result.output
    assert "expected 2, got 1" in result.output
    assert "after" not in result.output


def test_expect_neq_outside_echo_test_aborts_on_equality():
    result = run_echo('expectNeq("a", "a", "same");\nsay("after");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "same" in result.output
    assert "E2828" in result.output
    assert "after" not in result.output


def test_expect_eq_outside_echo_test_passes():
    result = run_echo('expectEq([1, 2], [1, 2], "lists");\nsay("yes");\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "yes"
