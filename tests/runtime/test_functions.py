from helpers import run_echo


def test_keyword_arguments():
    result = run_echo(
        """
fn describe(name: str, score: int) {
    say(name, score);
}

describe(score: 7, name: "Echo");
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Echo 7"


def test_lexical_read_without_use():
    result = run_echo(
        """
name: str = "Echo";
fn greet() {
    say(name);
}
greet();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Echo"


def test_use_mut_required_for_outer_assignment():
    result = run_echo(
        """
count: int = 0;
fn increment() {
    count = count + 1;
}
increment();
"""
    )
    assert result.exit_code == 1
    assert "without 'use mut'" in result.output


def test_use_mut_works_inside_nested_blocks():
    result = run_echo(
        """
count: int = 0;
fn bump() {
    use mut count;
    if true {
        count = count + 1;
    }
}
bump();
say(count);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_recursion():
    result = run_echo(
        """
fn fact(x: int) -> int {
    if x <= 1 { return 1; }
    return x * fact(x - 1);
}
say(fact(5));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "120"


def test_nested_function_closure():
    result = run_echo(
        """
fn outer() -> int {
    x: int = 5;
    fn inner() -> int {
        return x;
    }
    return inner();
}
say(outer());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "5"
