from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from conftest import run_echo_source
from main import run_file


def test_run_file_returns_error_for_missing_source(tmp_path):
    missing_file = tmp_path / "missing.echo"
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = run_file(str(missing_file), plain=True)

    assert exit_code == 1
    assert "Error: source file not found:" in stdout.getvalue()


def test_missing_semicolon_emits_friendly_hint(tmp_path):
    source = """
name: str = "Echo"
say(name);
"""

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 1
    assert "Syntax Error:" in output
    assert "Hint: You may be missing a semicolon ';'" in output


def test_invalid_type_assignment_reports_type_error(tmp_path):
    source = """
count: int = 1;
count = "oops";
"""

    exit_code, output = run_echo_source(tmp_path, source)

    assert exit_code == 1
    assert "Type Error: Cannot assign str to int variable 'count'" in output