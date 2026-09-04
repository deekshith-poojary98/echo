from helpers import run_echo


def test_for_expression_bounds_and_negative_start():
    result = run_echo(
        """
        n: int = 2;
for i: int in -1..n {
    say(i);
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["-1", "0", "1", "2"]


def test_for_by_zero_is_an_error():
    result = run_echo("for i: int in 0..3 by 0 { say(i); }\n")
    assert result.exit_code == 1
    assert "by 0" in result.output


def test_compound_assignment():
    result = run_echo("x: int = 1;\nx += 2;\nsay(x);\n")
    assert result.exit_code == 0
    assert result.output.strip() == "3"


def test_exclusive_range_and_step():
    result = run_echo(
        """
for i: int in 0...5 by 2 {
    say(i);
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["0", "2", "4"]


def test_break_and_continue_inside_while():
    result = run_echo(
        """
i: int = 0;
while true {
    i = i + 1;
    if i == 2 { continue; }
    say(i);
    if i == 3 { break; }
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["1", "3"]


def test_foreach_over_hash_iterates_keys():
    result = run_echo(
        """
data: hash = { "b": 2, "a": 1 };
foreach key: str in data {
    say(key);
}
"""
    )
    assert result.exit_code == 0
    assert set(result.lines) == {"a", "b"}


def test_else_if():
    result = run_echo(
        """
x: int = 2;
if x == 1 {
    say("one");
} else if x == 2 {
    say("two");
} else {
    say("other");
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "two"
