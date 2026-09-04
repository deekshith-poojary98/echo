from helpers import run_echo


def test_builtin_keyword_arguments_work_for_methods_and_standalone_calls():
    result = run_echo(
        """
nums: list = [1, 3];
nums.insertAt(value: 2, index: 1);
say(nums);

counts: list = [1, 2, 2, 3];
say(countOf(value: 2, items: counts));

data: hash = {};
say(data.ensure(default: 10, key: "score"));
say(data);
"""
    )
    assert result.exit_code == 0
    assert result.lines == [
        "[1, 2, 3]",
        "2",
        "10",
        '{"score": 10}',
    ]


def test_variadic_builtins_still_reject_keyword_arguments():
    result = run_echo('say(value: "Echo");')
    assert result.exit_code == 1
    assert "say() does not support keyword arguments" in result.output


def test_format_supports_positional_placeholders():
    result = run_echo('say("{0}-{1}-{}".format("Echo", 7, true));')
    assert result.exit_code == 0
    assert result.output.strip() == "Echo-7-Echo"


def test_pull_with_keyword_index_removes_expected_element():
    result = run_echo(
        """
nums: list = [10, 20, 30];
say(nums.pull(index: 1));
say(nums);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["20", "[10, 30]"]
