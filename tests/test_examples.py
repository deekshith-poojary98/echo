from __future__ import annotations

from pathlib import Path

import pytest

from conftest import REPO_ROOT, run_example


EXAMPLE_NAMES = sorted(path.name for path in (REPO_ROOT / "examples").glob("*.echo"))


@pytest.mark.parametrize("example_name", EXAMPLE_NAMES)
def test_example_program_executes_successfully(example_name):
    exit_code, output = run_example(example_name)

    assert exit_code == 0, f"{example_name} failed with output:\n{output}"