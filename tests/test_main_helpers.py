from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

import echo_cli
import main


def test_resolve_source_path_and_use_rich(monkeypatch):
    resolved = main._resolve_source_path(".")
    assert resolved.is_absolute()

    monkeypatch.setattr(main, "Console", object)
    monkeypatch.setattr(main, "Panel", object)
    assert main._use_rich(False) is True
    assert main._use_rich(True) is False

    monkeypatch.setattr(main, "Console", None)
    monkeypatch.setattr(main, "Panel", None)
    assert main._use_rich(False) is False


def test_print_error_and_hint_plain_and_rich(monkeypatch):
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        main._print_error("Error", "plain message", plain=True)
        main._print_hint("hint text", plain=True)
    assert "Error: plain message" in stdout.getvalue()
    assert "hint text" in stdout.getvalue()

    calls = []

    class DummyConsole:
        def print(self, panel):
            calls.append(panel)

    def dummy_panel(message, **kwargs):
        return {"message": message, **kwargs}

    monkeypatch.setattr(main, "Console", DummyConsole)
    monkeypatch.setattr(main, "Panel", dummy_panel)
    main._print_error("Error", "rich message", plain=False)
    main._print_hint("rich hint", plain=False)
    assert calls[0]["message"] == "rich message"
    assert calls[1]["message"] == "rich hint"


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Expected PUNCTUATION ;", "Hint: You may be missing a semicolon ';' at the end of the previous statement."),
        ("Expected PUNCTUATION : got KEYWORD(in)", "Hint: Loop variables must include a type, e.g. 'foreach item: dynamic in items { ... }' or 'for i: int in 0..10 { ... }'."),
        ("Expected PUNCTUATION {", "Hint: A block opening '{' is missing. Check function, if/else, while, for, or foreach headers."),
        ("Variable 'x' is not declared", "Hint: Declare variables with a type before assigning, e.g. 'name: str = \"Echo\";'."),
        ("Variable 'x' is not defined", "Hint: Check for typos and scope. If inside a function, use 'use var_name;' or 'use mut var_name;' for outer-scope variables."),
        ("missing a closing ')'", "Hint: You opened a function call with '(' but never closed it. Make sure every '(' has a matching ')'."),
        ("missing a closing ']'", "Hint: You opened a list with '[' but never closed it. Make sure every '[' has a matching ']'."),
        ("missing a closing '}'", "Hint: You opened a hash with '{' but never closed it. Make sure every '{' has a matching '}'."),
        ("Function hello not defined", "Hint: Check that the function is defined with 'fn name(...) { ... }' before calling it."),
        ("Cannot modify immutable import 'x'", "Hint: Use 'use mut variable_name;' inside the function before mutating that imported variable."),
        ("'return' statement outside function", "Hint: 'return' can only be used inside a function body."),
        ("'break' statement outside loop", "Hint: 'break' and 'continue' can only be used inside for/foreach/while loops."),
        ("Expected DATATYPE int", "Hint: Check the token shown after 'Expected ...'. The parser usually reports where structure first became invalid."),
        ("something else", None),
    ],
)
def test_build_hint_variants(message, expected):
    assert main._build_hint(message) == expected


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Expected PUNCTUATION ;, got IDENTIFIER(foo) at line 2, column 5", "Line 2, column 5: I expected ';' before 'foo'."),
        ("Expected PUNCTUATION :, got IDENTIFIER(foo) at line 2, column 5", "Line 2, column 5: I expected ':' before 'foo'."),
        ("Expected PUNCTUATION {, got IDENTIFIER(foo) at line 2, column 5", "Line 2, column 5: I expected '{' to start a code block before 'foo'."),
        ("Expected DATATYPE None, got IDENTIFIER(foo) at line 2, column 5", "Line 2, column 5: I expected datatype before 'foo'."),
        ("plain message", "plain message"),
    ],
)
def test_friendly_syntax_message_variants(message, expected):
    assert main._friendly_syntax_message(message) == expected


def test_run_file_exception_paths(monkeypatch, tmp_path):
    source_file = tmp_path / "program.echo"
    source_file.write_text("say(1);", encoding="utf-8")

    class DummyLexer:
        def read_source(self, _path):
            return []

    class DummyParser:
        def __init__(self, _tokens):
            pass

        def parse(self):
            return []

    class DummyInterpreter:
        def execute(self, _ast):
            return None

    monkeypatch.setattr(main, "Lexer", DummyLexer)
    monkeypatch.setattr(main, "Parser", DummyParser)
    monkeypatch.setattr(main, "Interpreter", DummyInterpreter)
    assert main.run_file(str(source_file), plain=True) == 0

    def run_case(exc):
        class RaisingInterpreter:
            def execute(self, _ast):
                raise exc

        monkeypatch.setattr(main, "Interpreter", RaisingInterpreter)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main.run_file(str(source_file), plain=True)
        return code, stdout.getvalue()

    assert run_case(SyntaxError("Expected PUNCTUATION ;, got IDENTIFIER(foo) at line 1, column 1"))[0] == 1
    assert "Syntax Error:" in run_case(SyntaxError("Expected PUNCTUATION ;, got IDENTIFIER(foo) at line 1, column 1"))[1]
    assert "Name Error:" in run_case(NameError("Variable 'x' is not defined"))[1]
    assert "Type Error:" in run_case(TypeError("bad type"))[1]
    assert "Execution Error:" in run_case(ValueError("bad value"))[1]
    assert "Execution Error:" in run_case(RuntimeError("bad runtime"))[1]
    assert "Execution Error:" in run_case(Exception("bad other"))[1]


def test_main_argument_parsing_and_echo_cli_forwarding(monkeypatch):
    calls = []

    def fake_run_file(source, plain=False):
        calls.append((source, plain))
        return 7

    monkeypatch.setattr(main, "run_file", fake_run_file)
    assert main.main(["program.echo"]) == 7
    assert main.main(["program.echo", "--plain"]) == 7
    assert calls == [("program.echo", False), ("program.echo", True)]

    monkeypatch.setattr(echo_cli, "_main", lambda: 42)
    assert echo_cli.main() == 42