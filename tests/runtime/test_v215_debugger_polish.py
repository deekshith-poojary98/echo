from helpers import assert_no_python_leak, run_echo


def test_abort_stack_nested_calls():
    result = run_echo(
        """
fn boom() {
    fail("x");
}
fn mid() {
    boom();
}
mid();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Stack:" in result.output
    assert "in boom" in result.output
    assert "in mid" in result.output
    # Newest frame first.
    boom_at = result.output.index("in boom")
    mid_at = result.output.index("in mid")
    assert boom_at < mid_at


def test_abort_top_level_has_no_stack_section():
    result = run_echo('fail("boom");\n')
    assert result.exit_code == 1
    assert "Stack:" not in result.output


def test_abort_stack_and_watched_together():
    result = run_echo(
        """
count: int = 3;
watch count;
fn boom() {
    fail("x");
}
boom();
"""
    )
    assert result.exit_code == 1
    assert "Stack:" in result.output
    assert "in boom" in result.output
    assert "Watched:" in result.output
    assert "count = 3" in result.output


def test_trace_prints_and_returns():
    result = run_echo(
        """
fn bump(n: int) -> int {
    return trace(n + 1);
}
say(bump(2));
say(7.trace());
"""
    )
    assert result.exit_code == 0, result.output
    assert "TRACE: 3 (in bump) at" in result.output
    assert "TRACE: 7 (in global) at" in result.output
    assert result.lines[-2:] == ["3", "7"] or (
        "3" in result.lines and "7" in result.lines
    )
