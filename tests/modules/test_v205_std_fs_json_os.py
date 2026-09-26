from pathlib import Path

from echo.runtime.host import Host
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_import_fs_helpers(tmp_path: Path) -> None:
    data = tmp_path / "note.txt"
    data.write_text("hello", encoding="utf-8")
    write_modules(
        tmp_path,
        {
            "app.echo": f"""
                import readFile from "std/fs";
                import fileExists from "std/fs";
                import pathJoin from "std/fs";
                path: str = pathJoin("{tmp_path.as_posix()}", "note.txt");
                say(fileExists(path));
                say(readFile(path));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "true\nhello")


def test_import_json_helpers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import parseJson from "std/json";
                import writeJson from "std/json";
                import parseJsonOr from "std/json";
                value: hash = parseJson("{\\"a\\": 1}");
                say(value["a"]);
                say(writeJson({ b: 2 }));
                say(parseJsonOr("nope", { ok: false })["ok"]);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "1\n{\"b\": 2}\nfalse")


def test_import_os_helpers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import envOr from "std/os";
                import args from "std/os";
                say(envOr("ECHO_V205_MISSING", "fallback"));
                say(type(args()));
            """,
        },
    )
    assert_success(
        run_entry(tmp_path, host=Host(environ={})),
        "fallback\nlist",
    )


def test_prelude_fs_json_os_still_work(tmp_path: Path) -> None:
    marker = tmp_path / "marker.txt"
    marker.write_text("ok", encoding="utf-8")
    write_modules(
        tmp_path,
        {
            "app.echo": f"""
                say(parseJson("{{\\"n\\": 3}}")["n"]);
                say(envOr("ECHO_V205_MISSING", "x"));
                say(fileExists("{marker.as_posix()}"));
            """,
        },
    )
    assert_success(run_entry(tmp_path, host=Host(environ={})), "3\nx\ntrue")


def test_std_fs_respects_allow_files(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import readFile from "std/fs";
                readFile("x.txt");
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path, host=Host(allow_files=False)), "E2801")
