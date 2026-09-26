from helpers import assert_no_python_leak, run_echo


def test_watch_includes_source_location():
    result = run_echo(
        """
count: int = 0;
watch count;
count = 1;
"""
    )
    assert result.exit_code == 0, result.output
    assert "WATCH: count changed to 1 (in global) at <test>:" in result.output


def test_abort_dumps_watched_bindings():
    result = run_echo(
        """
count: int = 7;
watch count;
fail("boom");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2825" in result.output or "boom" in result.output
    assert "Watched:" in result.output
    assert "count = 7" in result.output


def test_abort_without_watch_has_no_watched_section():
    result = run_echo('fail("boom");\n')
    assert result.exit_code == 1
    assert "Watched:" not in result.output


def test_watch_still_reports_mutations_with_location():
    result = run_echo(
        """
nums: list = [1, 2];
watch nums;
nums.push(3);
"""
    )
    assert result.exit_code == 0, result.output
    assert "WATCH: nums modified by push() to [1, 2, 3] (in global) at <test>:" in result.output
