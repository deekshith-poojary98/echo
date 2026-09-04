from contextlib import redirect_stdout
from io import StringIO

from echo import __version__
from echo.cli.main import main, run_file
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
