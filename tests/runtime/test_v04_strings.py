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
