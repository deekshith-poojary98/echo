from helpers import assert_no_python_leak, run_echo


def test_split_on_comma():
    result = run_echo('say("a,b,c".split(","));\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == '["a", "b", "c"]'


def test_split_standalone_and_empty_parts():
    result = run_echo('say(split("a,,b", ","));\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == '["a", "", "b"]'


def test_split_rejects_empty_separator():
    result = run_echo('say("abc".split(""));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "non-empty string" in result.output


def test_replace_all_occurrences():
    result = run_echo('say("foo foo food".replace("foo", "bar"));\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "bar bar bard"


def test_replace_rejects_empty_search():
    result = run_echo('say("abc".replace("", "-"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "non-empty" in result.output


def test_string_contains():
    result = run_echo(
        """
say("echo".contains("ch"));
say("echo".contains("x"));
say("echo".contains(""));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["true", "false", "true"]


def test_string_slice():
    result = run_echo('say("Echo".slice(1, 3));\nsay("Echo".slice(0, "Echo".length()));\n')
    assert result.exit_code == 0, result.output
    assert result.lines == ["ch", "Echo"]


def test_string_slice_out_of_range():
    result = run_echo('say("Echo".slice(1, 9));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Index Error" in result.output


def test_join_strings_and_empty_separator():
    result = run_echo(
        """
parts: list = ["a", "b", "c"];
say(parts.join(","));
say(join(["x", "y"], ""));
say([].join("-"));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["a,b,c", "xy", ""]


def test_join_rejects_non_string_items():
    result = run_echo('say([1, 2].join(","));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "list of strings" in result.output


def test_join_rejects_non_string_separator():
    result = run_echo('say(["a", "b"].join(1));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "separator must be a string" in result.output


def test_starts_with_and_ends_with():
    result = run_echo(
        """
say("echo".startsWith("ec"));
say("echo".startsWith("x"));
say("echo".startsWith(""));
say("echo".endsWith("ho"));
say("echo".endsWith("x"));
say(endsWith("echo", ""));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["true", "false", "true", "true", "false", "true"]


def test_starts_with_rejects_non_string_prefix():
    result = run_echo('say("echo".startsWith(1));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "requires a string" in result.output


def test_ends_with_rejects_non_string_suffix():
    result = run_echo('say("echo".endsWith(true));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "requires a string" in result.output
