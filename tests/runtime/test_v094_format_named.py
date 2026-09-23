from helpers import run_echo


def test_format_named_placeholders_from_hash():
    result = run_echo(
        """
say("Hello, {name}!".format({ name: "Echo" }));
say("{greeting}, {name}".format({ greeting: "Hi", name: "Ada" }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["Hello, Echo!", "Hi, Ada"]


def test_format_named_mixed_with_positional():
    result = run_echo(
        """
say("{0} scored {points}".format("Ada", { points: 42 }));
say("{}-{label}-{}".format("a", "c", { label: "b" }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["Ada scored 42", "a-b-c"]


def test_format_named_standalone_builtin():
    result = run_echo('say(format("Score: {score}", { score: 7 }));')
    assert result.exit_code == 0
    assert result.output.strip() == "Score: 7"


def test_format_named_reuses_key():
    result = run_echo('say("{x}-{x}".format({ x: 1 }));')
    assert result.exit_code == 0
    assert result.output.strip() == "1-1"


def test_format_named_missing_hash_errors():
    result = run_echo('say("{name}".format("Echo"));')
    assert result.exit_code == 1
    assert "trailing hash" in result.output
    assert "E2306" in result.output


def test_format_named_missing_key_errors():
    result = run_echo('say("{name}".format({ other: 1 }));')
    assert result.exit_code == 1
    assert "missing named placeholder" in result.output
    assert "E2307" in result.output


def test_format_positional_still_works():
    result = run_echo('say("{0}-{1}-{}".format("Echo", 7, true));')
    assert result.exit_code == 0
    assert result.output.strip() == "Echo-7-Echo"
