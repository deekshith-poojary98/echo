from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from echo.cli.main import main
from echo.std import list_std_modules, resolve_std_root, std_root


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_std_lists_install_tree_modules():
    code, output = _run_main(["std"])
    assert code == 0
    lines = [line for line in output.splitlines() if line.strip()]
    expected = list_std_modules()
    assert lines == expected
    assert "std/meta" in lines
    assert "std/math" in lines
    assert "std/yaml" in lines
    assert lines == sorted(lines)


def test_std_count():
    code, output = _run_main(["std", "--count"])
    assert code == 0
    assert output.strip() == str(len(list_std_modules()))


def test_std_path():
    code, output = _run_main(["std", "--path"])
    assert code == 0
    assert Path(output.strip()) == std_root()


def test_std_exports_includes_math_and_meta():
    code, output = _run_main(["std", "--exports"])
    assert code == 0
    text = output
    assert "std/math" in text
    assert "  abs" in text
    assert "  floor" in text
    assert "std/meta" in text
    assert "  stdOk" in text
    assert "  stdName" in text


def test_std_respects_echo_std_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    custom = tmp_path / "std"
    custom.mkdir()
    (custom / "demo.echo").write_text("export fn demo() -> int { return 1; }\n", encoding="utf-8")
    monkeypatch.setenv("ECHO_STD_ROOT", str(custom))
    assert resolve_std_root() == custom.resolve()
    code, output = _run_main(["std"])
    assert code == 0
    assert output.strip() == "std/demo"
    code, output = _run_main(["std", "--exports"])
    assert code == 0
    assert "std/demo" in output
    assert "  demo" in output


def test_top_level_help_mentions_std():
    stdout = StringIO()
    with redirect_stdout(stdout), pytest.raises(SystemExit) as caught:
        main(["-h"])
    assert caught.value.code == 0
    output = stdout.getvalue()
    assert "std" in output
    assert "builtins" in output
