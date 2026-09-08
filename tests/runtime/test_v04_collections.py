from helpers import assert_no_python_leak, run_echo


def test_list_contains_uses_echo_equality():
    result = run_echo(
        """
say([1, 2, 3].contains(2));
say([1, 2].contains(9));
say([[1], [2]].contains([1]));
say([true].contains(1));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["true", "false", "true", "false"]


def test_hash_has_key():
    result = run_echo(
        """
user: hash = { name: "Ada" };
say(user.has("name"));
say(user.has("age"));
say(has(items: user, key: "name"));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["true", "false", "true"]


def test_hash_has_rejects_non_string_key():
    result = run_echo("say({ a: 1 }.has(1));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "key must be a string" in result.output


def test_list_slice_exclusive_end():
    result = run_echo(
        """
nums: list = [1, 2, 3, 4];
mid: list = nums.slice(1, 3);
say(mid);
say(nums);
say(nums.slice(0, nums.length()));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["[2, 3]", "[1, 2, 3, 4]", "[1, 2, 3, 4]"]


def test_slice_does_not_share_identity():
    result = run_echo(
        """
nums: list = [1, 2, 3];
mid: list = nums.slice(0, 2);
mid.push(9);
say(nums);
say(mid);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["[1, 2, 3]", "[1, 2, 9]"]


def test_slice_rejects_negative_and_bool():
    result = run_echo("say([1, 2].slice(-1, 2));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Index Error" in result.output


def test_slice_rejects_bool_bound():
    result = run_echo("say([1, 2].slice(false, 1));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_standalone_slice():
    result = run_echo("say(slice(items: [10, 20, 30], start: 0, end: 2));\n")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "[10, 20]"
