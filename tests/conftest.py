from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from main import run_file  # noqa: E402


def run_echo_source(tmp_path: Path, source: str, plain: bool = True) -> tuple[int, str]:
    source_file = tmp_path / "program.echo"
    source_file.write_text(source, encoding="utf-8")

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = run_file(str(source_file), plain=plain)
    return exit_code, stdout.getvalue()


def run_example(example_name: str, plain: bool = True) -> tuple[int, str]:
    example_path = REPO_ROOT / "examples" / example_name
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = run_file(str(example_path), plain=plain)
    return exit_code, stdout.getvalue()