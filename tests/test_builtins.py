from __future__ import annotations

from conftest import run_echo_source


def test_builtin_keyword_arguments_work_for_methods_and_standalone_calls(tmp_path):
    source = """
nums: list = [1, 3];
nums.insertAt(value: 2, index: 1);
say(nums);

counts: list = [1, 2, 2, 3];
say(countOf(value: 2, items: counts));

data: hash = {};
say(data.ensure(default: 10, key: "score"));
say(data);
"""

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 0
    assert output.splitlines() == [
        "[1, 2, 3]",
        "2",
        "10",
        '{"score": 10}',
    ]


def test_variadic_builtins_still_reject_keyword_arguments(tmp_path):
    exit_code, output = run_echo_source(tmp_path, 'say(value: "Echo");')

    assert exit_code == 1
    assert "Type Error: say() does not support keyword arguments" in output


def test_format_supports_positional_placeholders(tmp_path):
    source = 'say("{0}-{1}-{}".format("Echo", 7, true));'

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 0
    assert output.strip() == "Echo-7-Echo"


def test_pull_with_keyword_index_removes_expected_element(tmp_path):
    source = """
nums: list = [10, 20, 30];
say(nums.pull(index: 1));
say(nums);
"""

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 0
    assert output.splitlines() == ["20", "[10, 30]"]