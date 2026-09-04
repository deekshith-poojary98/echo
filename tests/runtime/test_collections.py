from helpers import run_echo


def test_find_missing_returns_minus_one():
    result = run_echo('nums: list = [1];\nsay(nums.find(99));\n')
    assert result.exit_code == 0
    assert result.output.strip() == "-1"


def test_reverse_mutates_list():
    result = run_echo(
        """
nums: list = [1, 2, 3];
nums.reverse();
say(nums);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2, 3]".replace("1, 2, 3", "3, 2, 1")


def test_builtin_keyword_arguments():
    result = run_echo(
        """
nums: list = [1, 3];
nums.insertAt(value: 2, index: 1);
say(nums);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2, 3]"


def test_format_method_and_standalone():
    result = run_echo(
        """
say("{0}-{1}-{}".format("Echo", 7, true));
say(format("Hello {}", "Echo"));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["Echo-7-Echo", "Hello Echo"]
