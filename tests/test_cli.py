from helpers import run_echo
from echo.cli.main import run_file


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
