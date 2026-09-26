from pathlib import Path

from echo.runtime.builtins import (
    PEELED_STD_BUILTIN_NAMES,
    builtin_names,
    core_builtin_names,
    prelude_builtin_names,
)
from echo.runtime.host import Host
from helpers import run_echo
from modules.harness import assert_success, run_entry, write_modules


def test_peeled_names_are_subset_of_builtins() -> None:
    assert PEELED_STD_BUILTIN_NAMES <= builtin_names()
    assert core_builtin_names() == builtin_names() - PEELED_STD_BUILTIN_NAMES
    assert prelude_builtin_names(require_std=False) == builtin_names()
    assert prelude_builtin_names(require_std=True) == core_builtin_names()
    assert "say" in core_builtin_names()
    assert "httpGet" not in core_builtin_names()
    assert "readFile" not in core_builtin_names()


def test_require_std_hides_peeled_prelude_name() -> None:
    result = run_echo('say(httpOk(200));\n', host=Host(require_std=True))
    assert result.exit_code == 1
    assert "httpOk" in result.output.lower() or "not defined" in result.output.lower() or "E200" in result.output


def test_require_std_still_allows_core_prelude() -> None:
    result = run_echo('say(1 + 1);\n', host=Host(require_std=True))
    assert result.exit_code == 0
    assert result.output.strip() == "2"


def test_require_std_import_from_std_http(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import httpOk from "std/http";
                say(httpOk(200));
            """,
        },
    )
    assert_success(run_entry(tmp_path, host=Host(require_std=True)), "true")


def test_require_std_import_from_std_json(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import parseJson from "std/json";
                say(parseJson("{\\"n\\": 4}")["n"]);
            """,
        },
    )
    assert_success(run_entry(tmp_path, host=Host(require_std=True)), "4")


def test_default_host_still_has_peeled_prelude() -> None:
    result = run_echo("say(httpOk(404));\nsay(minutes(1));\n")
    assert result.exit_code == 0
    assert result.output.strip() == "false\n60"


def test_require_std_cli_flag(tmp_path: Path) -> None:
    app = tmp_path / "app.echo"
    app.write_text('say(httpOk(200));\n', encoding="utf-8")
    from contextlib import redirect_stdout
    from io import StringIO

    from echo.cli.main import main

    out = StringIO()
    with redirect_stdout(out):
        code = main(["--require-std", "--plain", str(app)])
    text = out.getvalue()
    assert code == 1
    assert "httpOk" in text or "not defined" in text.lower() or "E200" in text
