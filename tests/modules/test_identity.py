from pathlib import Path

import pytest

from modules.harness import assert_module_not_found, assert_success, run_entry, write_modules


def test_every_echo_file_is_a_module(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                x: int = 10;
                say("math-module");
            """,
            "app.echo": """
                say("entry-module");
            """,
        },
    )
    result = run_entry(tmp_path, "app.echo")
    assert_success(result, "entry-module")
    other = run_entry(tmp_path, "math.echo")
    assert_success(other, "math-module")


def test_cli_file_is_the_entry_module(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "first.echo": 'say("first");',
            "second.echo": 'say("second");',
        },
    )
    assert_success(run_entry(tmp_path, "first.echo"), "first")
    assert_success(run_entry(tmp_path, "second.echo"), "second")


def test_echo_extension_is_implied(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
            """,
            "app.echo": """
                import add from "math";
                say(add(2, 3));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "5")


def test_relative_imports_resolve_beside_the_importer(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "nested/math.echo": """
                export fn tag() -> str {
                    return "nested";
                }
            """,
            "math.echo": """
                export fn tag() -> str {
                    return "root";
                }
            """,
            "nested/app.echo": """
                import tag from "math";
                say(tag());
            """,
            "app.echo": """
                import tag from "math";
                say(tag());
            """,
        },
    )
    assert_success(run_entry(tmp_path, "app.echo"), "root")
    assert_success(run_entry(tmp_path, "nested/app.echo"), "nested")


def test_missing_sibling_is_not_found_in_another_directory(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "lib/math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
            """,
            "app.echo": """
                import add from "math";
                say(add(2, 3));
            """,
        },
    )
    assert_module_not_found(run_entry(tmp_path))


def test_resolved_absolute_path_defines_module_identity(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": """
                export hits: list = [];
                say("loaded");
            """,
            "left.echo": """
                import hits from "common";
                export fn mark_left() {
                    hits.push("L");
                }
            """,
            "right.echo": """
                import hits from "common";
                export fn mark_right() {
                    hits.push("R");
                }
            """,
            "app.echo": """
                import mark_left from "left";
                import mark_right from "right";
                import hits from "common";
                mark_left();
                mark_right();
                say(hits);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "loaded\n[L, R]")


def test_equivalent_paths_resolve_to_one_module_identity(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export box: list = [];
                say("data");
            """,
            "via_name.echo": """
                import box from "data";
                export fn from_name() -> list {
                    return box;
                }
            """,
            "app.echo": """
                import from_name from "via_name";
                import box from "data";
                from_name().push(7);
                say(box);
            """,
        },
    )
    link = tmp_path / "alias.echo"
    try:
        link.symlink_to(tmp_path / "data.echo")
    except OSError:
        pytest.skip("symlinks are unavailable")

    write_modules(
        tmp_path,
        {
            "via_alias.echo": """
                import box from "alias";
                export fn from_alias() -> list {
                    return box;
                }
            """,
            "app.echo": """
                import from_name from "via_name";
                import from_alias from "via_alias";
                from_name().push(1);
                say(from_alias());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "data\n[1]")
