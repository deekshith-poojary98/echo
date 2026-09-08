from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from textwrap import dedent

from echo.cli.main import run_file
from echo.runtime.host import Host
from helpers import ExecutionResult, PYTHON_EXCEPTION_NAMES, assert_no_python_leak


def write_modules(root: Path, files: dict[str, str]) -> Path:
    for relative, source in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(source).strip() + "\n", encoding="utf-8")
    return root


def run_entry(root: Path, entry: str = "app.echo", host: Host | None = None) -> ExecutionResult:
    path = (root / entry).resolve()
    stdout = StringIO()
    with redirect_stdout(stdout):
        try:
            exit_code = run_file(str(path), plain=True, host=host)
        except Exception as exc:  # noqa: BLE001 — leak detector
            raise AssertionError(
                f"Python exception leaked to the Echo user: {type(exc).__name__}: {exc}"
            ) from exc
    return ExecutionResult(exit_code, stdout.getvalue())


def assert_success(result: ExecutionResult, expected: str) -> None:
    assert_no_python_leak(result)
    assert result.exit_code == 0, result.output
    assert result.output.strip() == expected.strip(), result.output


def assert_echo_error(result: ExecutionResult, *needles: str) -> None:
    assert_no_python_leak(result)
    assert result.exit_code == 1, result.output
    lower = result.output.lower()
    assert "traceback (most recent call last)" not in lower, result.output
    for name in PYTHON_EXCEPTION_NAMES:
        assert f"{name}:" not in result.output, result.output
    for needle in needles:
        assert needle.lower() in lower, result.output
