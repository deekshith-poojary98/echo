from pathlib import Path

from modules.harness import assert_not_exported, assert_success, run_entry, write_modules


def test_names_are_private_by_default(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                fn hidden() -> int {
                    return 1;
                }
                x: int = 2;
            """,
            "app.echo": """
                import hidden from "math";
            """,
        },
    )
    assert_not_exported(run_entry(tmp_path), "hidden")


def test_export_makes_a_name_visible_to_importers(tmp_path: Path) -> None:
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


def test_private_functions_cannot_be_imported(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                fn subtract(a: int, b: int) -> int {
                    return a - b;
                }
            """,
            "app.echo": """
                import subtract from "math";
            """,
        },
    )
    assert_not_exported(run_entry(tmp_path), "subtract")


def test_private_variables_cannot_be_imported(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "config.echo": """
                export x: int = 10;
                y: int = 20;
            """,
            "app.echo": """
                import y from "config";
            """,
        },
    )
    assert_not_exported(run_entry(tmp_path), "y")


def test_multiple_exports_from_one_module_work(tmp_path: Path) -> None:
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
                export pi: int = 3;
            """,
            "app.echo": """
                import add from "math";
                import multiply from "math";
                import pi from "math";
                say(add(1, 2));
                say(multiply(3, 4));
                say(pi);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "3\n12\n3")
