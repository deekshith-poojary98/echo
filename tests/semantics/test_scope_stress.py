from helpers import run_echo


def test_lexical_read_uses_definition_site_not_caller():
    result = run_echo(
        """
x: int = 1;

fn readX() -> int {
    return x;
}

fn shadowThenCall() {
    x: int = 99;
    say(readX());
}

shadowThenCall();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_nested_closure_reads_through_two_function_scopes():
    result = run_echo(
        """
fn outer() {
    x: int = 4;
    fn mid() {
        fn inner() {
            say(x);
        }
        inner();
    }
    mid();
}
outer();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "4"


def test_recursive_nested_function_resolves_itself():
    result = run_echo(
        """
fn outer() {
    fn fact(n: int) -> int {
        if n <= 1 { return 1; }
        return n * fact(n - 1);
    }
    say(fact(5));
}
outer();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "120"


def test_same_name_at_three_levels_resolves_innermost():
    result = run_echo(
        """
x: int = 1;
fn f() {
    x: int = 2;
    fn g() {
        x: int = 3;
        say(x);
    }
    g();
    say(x);
}
f();
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "2", "1"]


def test_block_local_does_not_leak_and_does_not_clobber_outer():
    result = run_echo(
        """
x: int = 1;
if true {
    x: int = 2;
    say(x);
}
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["2", "1"]


def test_assignment_in_block_updates_enclosing_binding():
    result = run_echo(
        """
x: int = 1;
if true {
    x = 2;
}
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "2"


def test_for_loop_variable_does_not_leak():
    result = run_echo(
        """
for i: int in 0..1 {
    say(i);
}
say(i);
"""
    )
    assert result.exit_code == 1
    assert "not defined" in result.output
    assert "0" not in result.output.split("Semantic Error")[0]


def test_foreach_variable_does_not_leak():
    result = run_echo(
        """
foreach item: int in [1] {
    say(item);
}
say(item);
"""
    )
    assert result.exit_code == 1
    assert "not defined" in result.output


def test_function_inside_loop_captures_current_iteration_binding():
    result = run_echo(
        """
for i: int in 1..1 {
    fn inner() {
        say(i);
    }
    inner();
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_sibling_nested_functions_do_not_see_each_others_locals():
    result = run_echo(
        """
fn outer() {
    fn left() {
        secret: int = 7;
    }
    fn right() {
        say(secret);
    }
    left();
    right();
}
outer();
"""
    )
    assert result.exit_code == 1
    assert "not defined" in result.output


def test_null_local_does_not_fall_through_to_parent_from_nested_function():
    result = run_echo(
        """
x: dynamic = 1;
fn outer() {
    x: dynamic = null;
    fn inner() {
        say(x);
    }
    inner();
}
outer();
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["null", "1"]
