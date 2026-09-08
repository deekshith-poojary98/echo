from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path

from echo.cli.main import run_source
from echo.runtime.host import Host


REPO_ROOT = Path(__file__).resolve().parents[1]

PYTHON_EXCEPTION_NAMES = (
    "ValueError",
    "TypeError",
    "IndexError",
    "KeyError",
    "AttributeError",
    "NameError",
    "ZeroDivisionError",
    "RuntimeError",
    "StopIteration",
)


@dataclass
class ExecutionResult:
    exit_code: int
    output: str

    @property
    def lines(self) -> list[str]:
        return self.output.splitlines()


def run_echo(source: str, *, filename: str = "<test>", host: Host | None = None) -> ExecutionResult:
    stdout = StringIO()
    with redirect_stdout(stdout):
        try:
            exit_code = run_source(source, filename=filename, plain=True, host=host)
        except Exception as exc:  # noqa: BLE001 — leak detector
            raise AssertionError(
                f"Python exception leaked to the Echo user: {type(exc).__name__}: {exc}"
            ) from exc
    return ExecutionResult(exit_code, stdout.getvalue())


def assert_no_python_leak(result: ExecutionResult) -> None:
    for name in PYTHON_EXCEPTION_NAMES:
        assert f"{name}:" not in result.output, result.output
        assert f"{name}(" not in result.output, result.output
    lower = result.output.lower()
    assert "invalid literal" not in lower, result.output
    assert "not supported between instances" not in lower, result.output
    assert "object is not iterable" not in lower, result.output
    assert "traceback (most recent call last)" not in lower, result.output


def run_echo_file(path: Path) -> ExecutionResult:
    source = path.read_text(encoding="utf-8")
    return run_echo(source, filename=str(path))
