from contextlib import redirect_stdout
from io import StringIO

from echo.cli.main import main
from helpers import ExecutionResult, assert_no_python_leak


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_check_clean_file_succeeds_silently(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text('say("hello");\n', encoding="utf-8")
    code, output = _run_main(["check", str(app), "--plain"])
    assert code == 0
    assert output == ""


def test_check_reports_parse_error(tmp_path):
    app = tmp_path / "bad.echo"
    app.write_text("say(1)\n", encoding="utf-8")
    code, output = _run_main(["check", str(app), "--plain"])
    result = ExecutionResult(code, output)
    assert code == 1
    assert_no_python_leak(result)
    assert "Error" in output
    assert str(app.resolve()) in output


def test_check_directory_recurses_echo_files(tmp_path):
    nested = tmp_path / "src" / "inner"
    nested.mkdir(parents=True)
    ok = tmp_path / "src" / "ok.echo"
    bad = nested / "bad.echo"
    ignored = tmp_path / "src" / "skip.txt"
    ok.write_text('say("ok");\n', encoding="utf-8")
    bad.write_text("say(1)\n", encoding="utf-8")
    ignored.write_text("say(1)\n", encoding="utf-8")
    code, output = _run_main(["check", str(tmp_path / "src"), "--plain"])
    result = ExecutionResult(code, output)
    assert code == 1
    assert_no_python_leak(result)
    assert str(bad.resolve()) in output
    assert str(ok.resolve()) not in output
    assert "skip.txt" not in output


def test_check_directory_continues_after_a_failure(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    ok = src / "ok.echo"
    first = src / "a_bad.echo"
    second = src / "z_bad.echo"
    ok.write_text('say("ok");\n', encoding="utf-8")
    first.write_text("say(1)\n", encoding="utf-8")
    second.write_text("fn add(a: int, b: int) -> int { return a + b; }\nsay(add(1));\n", encoding="utf-8")
    code, output = _run_main(["check", str(src), "--plain"])
    assert code == 1
    assert str(first.resolve()) in output
    assert str(second.resolve()) in output
    assert "parameter 'b'" in output


def test_check_multiple_explicit_paths(tmp_path):
    first = tmp_path / "one.echo"
    second = tmp_path / "two.echo"
    first.write_text("say(1)\n", encoding="utf-8")
    second.write_text("fn add(a: int, b: int) -> int { return a + b; }\nsay(add(1));\n", encoding="utf-8")
    code, output = _run_main(["check", str(first), str(second), "--plain"])
    assert code == 1
    assert str(first.resolve()) in output
    assert str(second.resolve()) in output


def test_check_clean_directory_exits_zero(tmp_path):
    nested = tmp_path / "src" / "inner"
    nested.mkdir(parents=True)
    one = tmp_path / "src" / "one.echo"
    two = nested / "two.echo"
    one.write_text('say("one");\n', encoding="utf-8")
    two.write_text('say("two");\n', encoding="utf-8")
    code, output = _run_main(["check", str(tmp_path / "src"), "--plain"])
    assert code == 0
    assert output == ""


def test_check_missing_path_exits_one(tmp_path):
    missing = tmp_path / "missing.echo"
    code, output = _run_main(["check", str(missing), "--plain"])
    assert code == 1
    assert "source file not found" in output


def test_check_no_path_prints_help_and_fails():
    code, output = _run_main(["check"])
    assert code == 2
    assert "usage" in output.lower()
    assert "echo check" in output


def test_check_dot_echo_still_runs_the_file(tmp_path):
    app = tmp_path / "check.echo"
    app.write_text('say("ran");\n', encoding="utf-8")
    code, output = _run_main([str(app), "--plain"])
    assert code == 0
    assert output.strip() == "ran"
