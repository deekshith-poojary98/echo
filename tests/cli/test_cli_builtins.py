from contextlib import redirect_stdout
from io import StringIO

import pytest

from echo import __version__
from echo.cli.main import main
from echo.runtime.builtins import builtin_names


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_builtins_lists_sorted_runtime_names():
    code, output = _run_main(["builtins"])
    assert code == 0
    lines = [line for line in output.splitlines() if line.strip()]
    expected = sorted(builtin_names())
    assert lines == expected
    assert "base64Encode" in lines
    assert "httpGet" in lines
    assert "say" in lines


def test_builtins_count():
    code, output = _run_main(["builtins", "--count"])
    assert code == 0
    assert output.strip() == str(len(builtin_names()))


def test_version_short_flag():
    code, output = _run_main(["-V"])
    assert code == 0
    assert output.strip() == f"Echo {__version__}"


def test_top_level_help_mentions_builtins():
    stdout = StringIO()
    with redirect_stdout(stdout), pytest.raises(SystemExit) as caught:
        main(["-h"])
    assert caught.value.code == 0
    output = stdout.getvalue()
    assert "builtins" in output
    assert "Subcommands" in output
