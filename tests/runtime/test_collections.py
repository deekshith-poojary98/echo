from helpers import run_echo


def test_find_missing_returns_minus_one():
    result = run_echo('nums: list = [1];\nsay(nums.find(99));\n')
    assert result.exit_code == 0
    assert result.output.strip() == "-1"


def test_find_count_remove_use_echo_equality():
    result = run_echo(
        """
flags: list = [true];
say(flags.find(1));
say(flags.countOf(true));
say(flags.countOf(1));
nums: list = [true, 1, true];
nums.removeValue(1);
say(nums);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["-1", "1", "0", "[true, true]"]


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


def test_clone_is_deep():
    result = run_echo(
        """
inner: list = [1];
outer: list = [inner];
copied: list = outer.clone();
inner.push(2);
say(copied);
say(outer);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[1]]", "[[1, 2]]"]


def test_clone_hash_nested_is_deep():
    result = run_echo(
        """
inner: hash = { n: 1 };
outer: hash = { child: inner };
copied: hash = outer.clone();
inner["n"] = 9;
say(copied["child"]["n"]);
say(outer["child"]["n"]);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["1", "9"]


def test_string_reverse_does_not_mutate():
    result = run_echo(
        """
s: str = "ab";
say(s.reverse());
say(s);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["ba", "ab"]


def test_order_accepts_a_function_name():
    result = run_echo(
        """
fn byValue(a: int, b: int) -> int {
    return a - b;
}
nums: list = [3, 1, 2];
nums.order("byValue");
say(nums);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2, 3]"


def test_watch_reports_index_assignment():
    result = run_echo(
        """
nums: list = [1];
watch nums;
nums[0] = 9;
"""
    )
    assert result.exit_code == 0
    assert "WATCH:" in result.output
    assert "9" in result.output
