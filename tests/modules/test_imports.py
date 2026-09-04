from pathlib import Path

from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_selective_import_binds_the_selected_export(tmp_path: Path) -> None:
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


def test_non_selected_exports_are_not_introduced(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                export fn multiply(a: int, b: int) -> int {
                    return a * b;
                }
            """,
            "app.echo": """
                import add from "math";
                say(multiply(2, 3));
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "multiply")


def test_importing_an_unknown_export_fails(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
            """,
            "app.echo": """
                import missing from "math";
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "missing")


def test_imported_names_appear_in_importer_module_scope(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn square(x: int) -> int {
                    return x * x;
                }
            """,
            "app.echo": """
                import square from "math";
                fn use_imported() -> int {
                    return square(4);
                }
                say(use_imported());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "16")


def test_no_namespace_access_exists(tmp_path: Path) -> None:
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
                say(math.add(2, 3));
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "math")
