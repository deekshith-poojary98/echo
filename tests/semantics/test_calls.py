from helpers import run_echo


def test_calling_a_variable_is_semantic():
    result = run_echo(
        """
x: int = 10;
x();
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "not a function" in result.output


def test_missing_user_function_argument_is_semantic():
    result = run_echo(
        """
fn add(a: int, b: int) -> int { return a + b; }
say(add(1));
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "parameter 'b'" in result.output


def test_extra_user_function_argument_is_semantic():
    result = run_echo(
        """
fn identity(a: int) -> int { return a; }
say(identity(1, 2));
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "expected at most 1 argument" in result.output


def test_semantic_errors_have_no_runtime_side_effects():
    result = run_echo(
        """
say("SHOULD_NOT_PRINT");
return 1;
"""
    )
    assert result.exit_code == 1
    assert "SHOULD_NOT_PRINT" not in result.output
    assert "outside function" in result.output
