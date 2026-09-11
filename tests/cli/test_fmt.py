from contextlib import redirect_stdout
from io import StringIO

from echo.cli.main import main
from helpers import ExecutionResult, assert_no_python_leak


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_fmt_rewrites_in_place(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text("x:int=1;\n", encoding="utf-8")
    code, output = _run_main(["fmt", str(app), "--plain"])
    assert code == 0
    assert output == ""
    assert app.read_text(encoding="utf-8") == "x: int = 1;\n"


def test_fmt_check_dirty_exits_one_and_does_not_write(tmp_path):
    app = tmp_path / "app.echo"
    original = "x:int=1;\n"
    app.write_text(original, encoding="utf-8")
    code, output = _run_main(["fmt", "--check", str(app), "--plain"])
    assert code == 1
    assert str(app.resolve()) in output
    assert app.read_text(encoding="utf-8") == original


def test_fmt_check_clean_exits_zero(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text("x: int = 1;\n", encoding="utf-8")
    code, output = _run_main(["fmt", "--check", str(app), "--plain"])
    assert code == 0
    assert output == ""
    assert app.read_text(encoding="utf-8") == "x: int = 1;\n"


def test_fmt_dot_echo_still_runs_the_file(tmp_path):
    app = tmp_path / "fmt.echo"
    app.write_text('say("ran");\n', encoding="utf-8")
    code, output = _run_main([str(app), "--plain"])
    assert code == 0
    assert output.strip() == "ran"


def test_fmt_directory_recurses_echo_files(tmp_path):
    nested = tmp_path / "src" / "inner"
    nested.mkdir(parents=True)
    one = tmp_path / "src" / "one.echo"
    two = nested / "two.echo"
    ignored = tmp_path / "src" / "skip.txt"
    one.write_text("x:int=1;\n", encoding="utf-8")
    two.write_text("y:int=2;\n", encoding="utf-8")
    ignored.write_text("x:int=1;\n", encoding="utf-8")
    code, output = _run_main(["fmt", str(tmp_path / "src"), "--plain"])
    assert code == 0
    assert output == ""
    assert one.read_text(encoding="utf-8") == "x: int = 1;\n"
    assert two.read_text(encoding="utf-8") == "y: int = 2;\n"
    assert ignored.read_text(encoding="utf-8") == "x:int=1;\n"


def test_fmt_parse_error_does_not_write(tmp_path):
    app = tmp_path / "bad.echo"
    original = "say(1)\n"
    app.write_text(original, encoding="utf-8")
    code, output = _run_main(["fmt", str(app), "--plain"])
    result = ExecutionResult(code, output)
    assert code == 1
    assert_no_python_leak(result)
    assert "Error" in output
    assert app.read_text(encoding="utf-8") == original


def test_fmt_no_path_prints_help_and_fails():
    code, output = _run_main(["fmt"])
    assert code == 2
    assert "usage" in output.lower()
    assert "echo fmt" in output
