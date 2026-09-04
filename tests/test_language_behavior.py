from helpers import run_echo


def test_user_defined_keyword_arguments_still_work():
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


def test_function_requires_use_mut_for_global_mutation():
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


def test_use_mut_allows_global_mutation_from_function():
    result = run_echo(
        """
count: int = 0;

fn increment() {
    use mut count;
    count = count + 1;
}

increment();
say(count);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_watch_reports_list_mutation():
    result = run_echo(
        """
nums: list = [1, 2];
watch nums;
nums.push(3);
"""
    )
    assert result.exit_code == 0
    assert "WATCH: nums modified by push() to [1, 2, 3] (in global)" in result.output
