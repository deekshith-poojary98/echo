from __future__ import annotations

from pathlib import Path

from helpers import ExecutionResult, run_echo, run_echo_file

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_echo_source(tmp_path: Path, source: str, plain: bool = True) -> tuple[int, str]:
    result = run_echo(source)
    return result.exit_code, result.output


def run_example(example_name: str, plain: bool = True) -> tuple[int, str]:
    result = run_echo_file(REPO_ROOT / "examples" / example_name)
    return result.exit_code, result.output
