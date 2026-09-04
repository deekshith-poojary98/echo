from helpers import assert_no_python_leak, run_echo


def test_mixed_positional_and_keyword_arguments_bind_in_order():
    result = run_echo(
        """
fn pair(a: int, b: int) {
    say(a, b);
}
pair(1, b: 2);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1 2"


def test_keyword_only_call_fills_all_parameters():
    result = run_echo(
        """
fn pair(a: int, b: int) {
    say(a, b);
}
pair(b: 2, a: 1);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1 2"


def test_missing_keyword_argument_is_semantic():
    result = run_echo(
        """
fn pair(a: int, b: int) {
    say(a, b);
}
pair(a: 1);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Semantic Error" in result.output
    assert "b" in result.output


def test_unexpected_keyword_argument_is_semantic():
    result = run_echo(
        """
fn pair(a: int, b: int) {
    say(a, b);
}
pair(1, extra: 2);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Semantic Error" in result.output
    assert "unexpected keyword" in result.output


def test_duplicate_keyword_argument_is_semantic():
    result = run_echo(
        """
fn identity(a: int) -> int { return a; }
say(identity(a: 1, a: 2));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Semantic Error" in result.output
    assert "multiple" in result.output


def test_positional_and_keyword_for_same_parameter_is_semantic():
    result = run_echo(
        """
fn pair(a: int, b: int) {
    say(a, b);
}
pair(1, a: 2);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Semantic Error" in result.output
    assert "multiple values" in result.output


def test_positional_argument_after_keyword_is_parse_error():
    result = run_echo(
        """
fn pair(a: int, b: int) {
    say(a, b);
}
pair(a: 1, 2);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Syntax Error" in result.output
    assert "Positional arguments cannot appear after keyword arguments" in result.output


def test_wrong_argument_type_is_type_error():
    result = run_echo(
        """
fn identity(a: int) -> int { return a; }
say(identity("nope"));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output
    assert "int" in result.output


def test_return_from_nested_block():
    result = run_echo(
        """
fn pick(flag: bool) -> int {
    if flag {
        return 7;
    }
    return 0;
}
say(pick(true));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "7"


def test_bare_return_yields_null():
    result = run_echo(
        """
fn nothing() -> dynamic {
    return;
}
say(nothing());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "null"


def test_void_function_cannot_return_a_value():
    result = run_echo(
        """
fn nothing() -> void {
    return 1;
}
nothing();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "void" in result.output


def test_return_without_annotation_is_semantic():
    result = run_echo(
        """
fn oops() {
    return 1;
}
oops();
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "Return type annotation required" in result.output


def test_inline_function():
    result = run_echo(
        """
fn square(x: int) -> int => x * x;
say(square(6));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "36"


def test_continue_outside_loop_is_semantic():
    result = run_echo("continue;\n")
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "outside loop" in result.output


def test_returning_a_nested_function_is_not_source_syntax():
    result = run_echo(
        """
fn make() {
    fn inner() {}
    return inner;
}
make();
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "Return type annotation required" in result.output


def test_wait_without_arguments_is_an_echo_error():
    result = run_echo("wait();\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output


def test_length_without_arguments_is_an_echo_error():
    result = run_echo("length();\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "length()" in result.output


def test_as_int_without_arguments_is_an_echo_error():
    result = run_echo("asInt();\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "asInt()" in result.output


def test_format_without_arguments_is_an_echo_error():
    result = run_echo("format();\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "format()" in result.output
