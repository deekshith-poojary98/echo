from contextlib import redirect_stdout
from io import StringIO

from echo import __version__
from echo.cli.main import check_file, main, run_file
from helpers import run_echo
from modules.harness import assert_success, run_entry, write_modules


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
