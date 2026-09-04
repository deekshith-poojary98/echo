from helpers import run_echo


def test_interpolation_at_start_and_escapes_in_fragments():
    result = run_echo(
        r"""
name: str = "Echo";
say("${name}\nnext");
say('value=${name}');
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["Echo", "next", "value=Echo"]


def test_newline_inside_quotes_is_lex_error():
    result = run_echo("say(\"oops\nthere\");\n")
    assert result.exit_code == 1
    assert "Unterminated string" in result.output or "Syntax Error" in result.output
