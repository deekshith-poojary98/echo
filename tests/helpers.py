from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path

from echo.cli.main import run_source


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ExecutionResult:
    exit_code: int
    output: str

    @property
    def lines(self) -> list[str]:
        return self.output.splitlines()


def run_echo(source: str, *, filename: str = "<test>") -> ExecutionResult:
    stdout = StringIO()
    with redirect_stdout(stdout):
        exit_code = run_source(source, filename=filename, plain=True)
    return ExecutionResult(exit_code, stdout.getvalue())


def run_echo_file(path: Path) -> ExecutionResult:
    source = path.read_text(encoding="utf-8")
    return run_echo(source, filename=str(path))
