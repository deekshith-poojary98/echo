from unittest.mock import patch

from helpers import assert_no_python_leak, run_echo


def test_read_line_returns_stdin_line():
    with patch("builtins.input", return_value="hello"):
        result = run_echo("say(readLine());\n")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "hello"


def test_read_line_eof_is_echo_error():
    with patch("builtins.input", side_effect=EOFError):
        result = run_echo("say(readLine());\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "end of input" in result.output
    assert "EOFError" not in result.output


def test_ask_returns_stdin_line():
    with patch("builtins.input", return_value="Ada"):
        result = run_echo('name: str = ask("Name: ");\nsay(name);\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "Ada"


def test_ask_stringifies_prompt_with_echo_spelling():
    seen: list[str] = []

    def _capture(prompt: object = "") -> str:
        seen.append(prompt)  # type: ignore[arg-type]
        return "ok"

    with patch("builtins.input", side_effect=_capture):
        result = run_echo("say(ask(true));\n")
    assert result.exit_code == 0, result.output
    assert seen == ["true"]
    assert result.output.strip() == "ok"


def test_ask_eof_is_echo_error():
    with patch("builtins.input", side_effect=EOFError):
        result = run_echo('name: str = ask("Name: ");\nsay(name);\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "end of input" in result.output
    assert "EOFError" not in result.output


def test_read_line_rejects_arguments():
    result = run_echo('say(readLine("prompt"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "takes no arguments" in result.output
