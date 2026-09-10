from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from echo import __version__
from echo.cli.main import check_file, main, run_file
from echo.runtime.interpreter import Interpreter
from helpers import ExecutionResult, assert_no_python_leak, run_echo
from modules.harness import assert_success, run_entry, write_modules


def _repl_input(lines):
    values = iter(lines)
    prompts = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        value = next(values)
        if isinstance(value, type) and issubclass(value, BaseException):
            raise value
        if isinstance(value, BaseException):
            raise value
        return value

    return fake_input, prompts


def test_run_file_returns_error_for_missing_source(tmp_path):
    missing = tmp_path / "missing.echo"
    assert run_file(str(missing), plain=True) == 1


def test_missing_semicolon_emits_friendly_hint():
    result = run_echo(
        """
name: str = "Echo"
say(name);
"""
    )
    assert result.exit_code == 1
    assert "Syntax Error" in result.output
    assert "semicolon" in result.output


def test_invalid_type_assignment_reports_type_error():
    result = run_echo(
        """
count: int = 1;
count = "oops";
"""
    )
    assert result.exit_code == 1
    assert "Cannot assign str to int variable 'count'" in result.output


def test_version_is_reported():
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["--version"])
    assert code == 0
    assert __version__ in stdout.getvalue()


def test_file_without_import_does_not_load_sibling(tmp_path):
    write_modules(
        tmp_path,
        {
            "unused.echo": 'say("unused");',
            "app.echo": 'say("only-entry");',
        },
    )
    assert_success(run_entry(tmp_path), "only-entry")


def test_file_with_import_loads_sibling(tmp_path):
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                say("math");
            """,
            "app.echo": """
                import add from "math";
                say(add(2, 3));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "math\n5")


def test_check_file_succeeds_silently(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text('say("hello");\n', encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = check_file(str(app), plain=True)
    assert code == 0
    assert stdout.getvalue() == ""


def test_check_reports_semantic_error(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text("fn add(a: int, b: int) -> int { return a + b; }\nsay(add(1));\n", encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["check", str(app), "--plain"])
    assert code == 1
    output = stdout.getvalue()
    assert "Semantic Error" in output
    assert "parameter 'b'" in output


def test_check_does_not_execute_imported_module(tmp_path):
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                say("math");
            """,
            "app.echo": """
                import add from "math";
                say(add(2, 3));
            """,
        },
    )
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["check", str(tmp_path / "app.echo"), "--plain"])
    assert code == 0
    assert stdout.getvalue() == ""


def test_check_dot_echo_still_runs_the_file(tmp_path):
    app = tmp_path / "check.echo"
    app.write_text('say("ran");\n', encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main([str(app), "--plain"])
    assert code == 0
    assert stdout.getvalue().strip() == "ran"


def test_repl_runs_source_and_exits_on_eof():
    stdout = StringIO()
    with patch("builtins.input", side_effect=["say(1);", EOFError]):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    output = stdout.getvalue()
    assert "1" in output
    assert f"Echo {__version__}" in output


def test_repl_keeps_going_after_error_then_exits():
    stdout = StringIO()
    with patch("builtins.input", side_effect=["say(1 / 0);", "say(2);", EOFError]):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    output = stdout.getvalue()
    assert "Error" in output
    assert "2" in output.splitlines()
    assert "Traceback" not in output


def test_repl_empty_line_is_ignored():
    stdout = StringIO()
    with patch("builtins.input", side_effect=["", "   ", "say(3);", EOFError]):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    assert "3" in stdout.getvalue().splitlines()
    assert "Syntax Error" not in stdout.getvalue()


def test_repl_single_line_if_runs():
    stdout = StringIO()
    with patch("builtins.input", side_effect=["if true { say(1); }", EOFError]):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    assert "1" in stdout.getvalue().splitlines()


def test_repl_continues_while_braces_are_unclosed():
    fake_input, prompts = _repl_input(
        [
            "if true {",
            "say(1);",
            "}",
            EOFError,
        ]
    )
    stdout = StringIO()
    with patch("builtins.input", fake_input):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    assert "1" in stdout.getvalue().splitlines()
    assert prompts[:3] == ["echo> ", "... ", "... "]


def test_repl_continues_unterminated_triple_string():
    fake_input, prompts = _repl_input(
        [
            'text: str = """',
            "hello",
            'world"""; say(text);',
            EOFError,
        ]
    )
    stdout = StringIO()
    with patch("builtins.input", fake_input):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    lines = [line for line in stdout.getvalue().splitlines() if line]
    assert lines[-2:] == ["hello", "world"]
    assert prompts[:3] == ["echo> ", "... ", "... "]


def test_repl_function_and_call_in_one_submission():
    fake_input, prompts = _repl_input(
        [
            "fn add(a: int, b: int) -> int {",
            "return a + b;",
            "} say(add(2, 3));",
            EOFError,
        ]
    )
    stdout = StringIO()
    with patch("builtins.input", fake_input):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    assert "5" in stdout.getvalue().splitlines()
    assert prompts[:3] == ["echo> ", "... ", "... "]


def test_repl_two_statements_on_one_line_run():
    stdout = StringIO()
    with patch("builtins.input", side_effect=["say(1); say(2);", EOFError]):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    lines = [line for line in stdout.getvalue().splitlines() if line]
    assert lines[-2:] == ["1", "2"]


def test_repl_missing_semicolon_is_echo_error_not_python():
    stdout = StringIO()
    with patch("builtins.input", side_effect=["say(1) say(2);", "say(3);", EOFError]):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0
    output = stdout.getvalue()
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert "Error" in output
    assert "3" in output.splitlines()


def test_repl_exit_builtin_returns_that_code():
    stdout = StringIO()
    with patch("builtins.input", side_effect=["exit(3);"]):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 3
    assert "Traceback" not in stdout.getvalue()


def test_repl_exit_zero_is_success():
    stdout = StringIO()
    with patch("builtins.input", side_effect=["exit(0);"]):
        with redirect_stdout(stdout):
            code = main(["--plain"])
    assert code == 0


def test_repl_unexpected_exception_does_not_kill_or_traceback():
    calls = {"n": 0}
    real_execute = Interpreter.execute

    def execute(self, program, env=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("boom")
        return real_execute(self, program, env)

    stdout = StringIO()
    with patch.object(Interpreter, "execute", execute):
        with patch("builtins.input", side_effect=["say(1);", "say(2);", EOFError]):
            with redirect_stdout(stdout):
                code = main(["--plain"])
    assert code == 0
    output = stdout.getvalue()
    assert "Traceback" not in output
    assert "ValueError" not in output
    assert "2" in output.splitlines()


def test_repl_ctrl_c_during_execute_keeps_prompt():
    calls = {"n": 0}
    real_execute = Interpreter.execute

    def execute(self, program, env=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise KeyboardInterrupt
        return real_execute(self, program, env)

    stdout = StringIO()
    with patch.object(Interpreter, "execute", execute):
        with patch("builtins.input", side_effect=["say(1);", "say(2);", EOFError]):
            with redirect_stdout(stdout):
                try:
                    code = main(["--plain"])
                except KeyboardInterrupt:
                    raise AssertionError("KeyboardInterrupt leaked from the REPL") from None
    assert code == 0
    assert "2" in stdout.getvalue().splitlines()
    assert "Traceback" not in stdout.getvalue()


def test_echo_test_passes_on_exit_zero(tmp_path):
    app = tmp_path / "ok.echo"
    app.write_text('say("ok");\n', encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["test", str(app), "--plain"])
    assert code == 0
    assert stdout.getvalue().strip() == "ok"


def test_echo_test_fails_on_nonzero(tmp_path):
    app = tmp_path / "bad.echo"
    app.write_text("say(1 / 0);\n", encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["test", str(app), "--plain"])
    output = stdout.getvalue()
    assert code == 1
    assert_no_python_leak(ExecutionResult(code, output))
    assert "Error" in output


def test_echo_test_dot_echo_still_runs_the_file(tmp_path):
    app = tmp_path / "test.echo"
    app.write_text('say("ran");\n', encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main([str(app), "--plain"])
    assert code == 0
    assert stdout.getvalue().strip() == "ran"


def test_echo_test_no_path_prints_help_and_fails():
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["test"])
    assert code == 2
    output = stdout.getvalue()
    assert "usage" in output.lower()
    assert "echo test" in output


def test_echo_test_missing_file_fails_clearly(tmp_path):
    missing = tmp_path / "missing.echo"
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["test", str(missing), "--plain"])
    assert code == 1
    output = stdout.getvalue()
    assert_no_python_leak(ExecutionResult(code, output))
    assert "source file not found" in output
    assert "Traceback" not in output


def test_echo_test_explicit_exit_zero_passes(tmp_path):
    app = tmp_path / "ok.echo"
    app.write_text("exit(0);\n", encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["test", str(app), "--plain"])
    assert code == 0


def test_echo_test_exit_two_is_failure(tmp_path):
    app = tmp_path / "bad.echo"
    app.write_text("exit(2);\n", encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["test", str(app), "--plain"])
    assert code == 2
    assert "Error" not in stdout.getvalue()


def test_echo_test_executes_imported_module(tmp_path):
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                say("math");
            """,
            "app.echo": """
                import add from "math";
                say(add(2, 3));
            """,
        },
    )
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["test", str(tmp_path / "app.echo"), "--plain"])
    assert code == 0
    assert stdout.getvalue().strip() == "math\n5"


def test_echo_test_failing_import_fails_the_test(tmp_path):
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                say(1 / 0);
            """,
            "app.echo": """
                import add from "math";
                say(add(2, 3));
            """,
        },
    )
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(["test", str(tmp_path / "app.echo"), "--plain"])
    output = stdout.getvalue()
    assert code == 1
    assert_no_python_leak(ExecutionResult(code, output))
    assert "Error" in output
