from helpers import run_echo


def test_return_outside_function_is_semantic():
    result = run_echo("return 1;\n")
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "outside function" in result.output


def test_break_outside_loop_is_semantic():
    result = run_echo("break;\n")
    assert result.exit_code == 1
    assert "outside loop" in result.output


def test_undefined_variable_is_semantic():
    result = run_echo("say(missing);\n")
    assert result.exit_code == 1
    assert "not defined" in result.output
