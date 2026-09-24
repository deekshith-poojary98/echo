from helpers import assert_no_python_leak, run_echo


def test_regex_match_find_replace_split():
    result = run_echo(
        """
say(regexMatch("hello 42", "\\\\d+"));
say(regexFind("hello 42", "\\\\d+"));
say(regexReplace("a1b2", "\\\\d", "X"));
say(regexSplit("a,b,c", ","));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["true", "42", "aXbX", '["a", "b", "c"]']


def test_regex_method_form():
    result = run_echo(
        """
say("abc123".regexMatch("[0-9]+"));
say("abc123".regexFind("[0-9]+"));
say("foo-bar".regexReplace("-", "_"));
say("one|two|three".regexSplit("\\\\|"));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["true", "123", "foo_bar", '["one", "two", "three"]']


def test_regex_find_returns_null_when_missing():
    result = run_echo('say(regexFind("hello", "\\\\d+"));\n')
    assert result.exit_code == 0
    assert result.output.strip() == "null"


def test_regex_match_false_when_missing():
    result = run_echo('say(regexMatch("hello", "\\\\d+"));\n')
    assert result.exit_code == 0
    assert result.output.strip() == "false"


def test_regex_replace_supports_groups():
    result = run_echo('say(regexReplace("ab-cd", "([a-z]+)-([a-z]+)", "\\\\2:\\\\1"));\n')
    assert result.exit_code == 0
    assert result.output.strip() == "cd:ab"


def test_regex_invalid_pattern_aborts():
    result = run_echo('say(regexMatch("x", "["));\n')
    assert result.exit_code == 1
    assert "invalid regex" in result.output
    assert "E2850" in result.output


def test_regex_type_errors():
    result = run_echo("say(regexMatch(1, \"a\"));\n")
    assert result.exit_code == 1
    assert "must be a string" in result.output


def test_regex_replace_invalid_group_is_echo_error_not_python():
    result = run_echo('say(regexReplace("hello", "(h)", "\\\\2"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "invalid regex replacement" in result.output
    assert "E2850" in result.output


def test_regex_replace_bad_escape_is_echo_error_not_python():
    result = run_echo('say(regexReplace("a", "a", "\\\\"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "invalid regex replacement" in result.output
    assert "E2850" in result.output


def test_regex_replace_unknown_named_group_is_echo_error_not_python():
    result = run_echo('say(regexReplace("hello", "(h)", "\\\\g<nope>"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "invalid regex replacement" in result.output
    assert "E2850" in result.output
