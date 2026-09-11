from contextlib import redirect_stdout
from io import StringIO

from echo.cli.main import main
from helpers import ExecutionResult, assert_no_python_leak


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_lint_reports_findings_and_exits_one(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text("x: int = 1;\nsay(2);\n", encoding="utf-8")
    code, output = _run_main(["lint", str(app), "--plain"])
    assert code == 1
    assert "unused-local" in output
    assert str(app.resolve()) in output
    assert "x" in output


def test_lint_clean_exits_zero(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text('say("ok");\n', encoding="utf-8")
    code, output = _run_main(["lint", str(app), "--plain"])
    assert code == 0
    assert output == ""


def test_lint_directory_recurses_echo_files(tmp_path):
    nested = tmp_path / "src" / "inner"
    nested.mkdir(parents=True)
    dirty = tmp_path / "src" / "one.echo"
    clean = nested / "two.echo"
    ignored = tmp_path / "src" / "skip.txt"
    dirty.write_text("x: int = 1;\nsay(1);\n", encoding="utf-8")
    clean.write_text('say("ok");\n', encoding="utf-8")
    ignored.write_text("x: int = 1;\n", encoding="utf-8")
    code, output = _run_main(["lint", str(tmp_path / "src"), "--plain"])
    assert code == 1
    assert "unused-local" in output
    assert str(dirty.resolve()) in output
    assert str(clean.resolve()) not in output
    assert "skip.txt" not in output


def test_lint_dot_echo_still_runs_the_file(tmp_path):
    app = tmp_path / "lint.echo"
    app.write_text('say("ran");\n', encoding="utf-8")
    code, output = _run_main([str(app), "--plain"])
    assert code == 0
    assert output.strip() == "ran"


def test_fail_dot_echo_still_runs_the_file(tmp_path):
    app = tmp_path / "fail.echo"
    app.write_text('say("ran");\n', encoding="utf-8")
    code, output = _run_main([str(app), "--plain"])
    assert code == 0
    assert output.strip() == "ran"


def test_lint_parse_error_matches_check_style(tmp_path):
    app = tmp_path / "bad.echo"
    app.write_text("say(1)\n", encoding="utf-8")
    code, output = _run_main(["lint", str(app), "--plain"])
    result = ExecutionResult(code, output)
    assert code == 1
    assert_no_python_leak(result)
    assert "Error" in output
    assert "unused-local" not in output


def test_lint_no_path_prints_help_and_fails():
    code, output = _run_main(["lint"])
    assert code == 2
    assert "usage" in output.lower()
    assert "echo lint" in output


def test_echo_test_fail_aborts(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text('fail("nope");\nsay("after");\n', encoding="utf-8")
    code, output = _run_main(["test", str(app), "--plain"])
    result = ExecutionResult(code, output)
    assert code == 1
    assert_no_python_leak(result)
    assert "nope" in output
    assert "E2825" in output
    assert "after" not in output
