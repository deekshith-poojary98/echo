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


def test_break_in_nested_function_inside_loop_is_semantic():
    # Nested functions used to inherit the enclosing loop's is_loop flag, so
    # this compiled and later leaked BreakSignal when inner() ran outside.
    result = run_echo(
        """
handlers: list = [];
for i: int in 0..1 {
    fn inner() -> void {
        break;
    }
    handlers.push(inner);
}
handlers[0]();
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "outside loop" in result.output
    assert "E1004" in result.output


def test_continue_in_nested_lambda_inside_loop_is_semantic():
    result = run_echo(
        """
handlers: list = [];
while true {
    handlers.push(fn() -> void { continue; });
    break;
}
handlers[0]();
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "outside loop" in result.output
    assert "E1004" in result.output


def test_undefined_variable_is_semantic():
    result = run_echo("say(missing);\n")
    assert result.exit_code == 1
    assert "not defined" in result.output
