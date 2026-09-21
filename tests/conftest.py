from __future__ import annotations

from pathlib import Path

from helpers import ExecutionResult, run_echo, run_echo_file

REPO_ROOT = Path(__file__).resolve().parents[1]

# Interactive examples need scripted answers for `ask` / `readLine`.
EXAMPLE_STDIN: dict[str, list[str]] = {
    "bank_account.echo": [
        "deposit",
        "100",
        "balance",
        "withdraw",
        "30",
        "withdraw",
        "abc",
        "w",
        "999",
        "exit",
    ],
}


def run_echo_source(tmp_path: Path, source: str, plain: bool = True) -> tuple[int, str]:
    result = run_echo(source)
    return result.exit_code, result.output


def run_example(example_name: str, plain: bool = True) -> tuple[int, str]:
    stdin = EXAMPLE_STDIN.get(example_name)
    result = run_echo_file(REPO_ROOT / "examples" / example_name, stdin_lines=stdin)
    return result.exit_code, result.output
