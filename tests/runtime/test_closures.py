from helpers import run_echo


def test_nested_function_reads_enclosing_local():
    result = run_echo(
        """
fn outer() -> int {
    x: int = 5;
    fn inner() -> int { return x; }
    return inner();
}
say(outer());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "5"


def test_captured_variable_mutation_requires_use_mut():
    result = run_echo(
        """
fn outer() {
    n: int = 0;
    fn bump() {
        n = n + 1;
    }
    bump();
}
outer();
"""
    )
    assert result.exit_code == 1
    assert "outer variable 'n'" in result.output
    assert "SHOULD_NOT" not in result.output


def test_captured_variable_mutation_with_use_mut():
    result = run_echo(
        """
fn outer() {
    n: int = 0;
    fn bump() {
        use mut n;
        n = n + 1;
    }
    bump();
    bump();
    say(n);
}
outer();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "2"


def test_nested_function_does_not_inherit_use_mut():
    result = run_echo(
        """
count: int = 0;
fn outer() {
    use mut count;
    fn inner() {
        count = count + 1;
    }
    inner();
}
outer();
"""
    )
    assert result.exit_code == 1
    assert "outer variable 'count'" in result.output


def test_function_inside_block_can_read_block_local():
    result = run_echo(
        """
if true {
    y: int = 7;
    fn inner() { say(y); }
    inner();
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "7"


def test_function_inside_block_is_not_visible_outside():
    result = run_echo(
        """
if true {
    fn foo() { say("hi"); }
    foo();
}
foo();
"""
    )
    assert result.exit_code == 1
    assert "Function 'foo' is not defined" in result.output
    assert "hi" not in result.output


def test_shadowing_does_not_mutate_outer():
    result = run_echo(
        """
x: int = 1;
fn f() {
    x: int = 2;
    say(x);
}
f();
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["2", "1"]


def test_sibling_function_cannot_see_locals():
    result = run_echo(
        """
fn a() { x: int = 1; }
fn b() { say(x); }
b();
"""
    )
    assert result.exit_code == 1
    assert "not defined" in result.output


def test_closure_over_parameter():
    result = run_echo(
        """
fn make_adder(base: int) {
    fn add(n: int) -> int { return base + n; }
    say(add(3));
}
make_adder(10);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "13"
