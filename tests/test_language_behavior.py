from __future__ import annotations

from conftest import run_echo_source


def test_user_defined_keyword_arguments_still_work(tmp_path):
    source = """
fn describe(name: str, score: int) {
    say(name, score);
}

describe(score: 7, name: "Echo");
"""

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 0
    assert output.strip() == "Echo 7"


def test_function_requires_use_mut_for_global_mutation(tmp_path):
    source = """
count: int = 0;

fn increment() {
    count = count + 1;
}

increment();
"""

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 1
    assert "Name Error: Variable 'count' used without 'use' statement in function" in output


def test_use_mut_allows_global_mutation_from_function(tmp_path):
    source = """
count: int = 0;

fn increment() {
    use mut count;
    count = count + 1;
}

increment();
say(count);
"""

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 0
    assert output.strip() == "1"


def test_watch_reports_list_mutation(tmp_path):
    source = """
nums: list = [1, 2];
watch nums;
nums.push(3);
"""

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 0
    assert "WATCH: nums modified by push() to [1, 2, 3] (in global)" in output