from pathlib import Path

from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_module_private_names_are_inaccessible_to_importers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                secret: int = 42;
                export fn answer() -> int {
                    return secret;
                }
            """,
            "app.echo": """
                import answer from "math";
                say(answer());
                say(secret);
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "secret")
    assert "42" not in result.output


def test_importer_locals_are_invisible_to_imported_functions(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn read() -> int {
                    return secret;
                }
            """,
            "app.echo": """
                secret: int = 42;
                import read from "math";
                say(read());
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "secret")
    assert result.output.strip() != "42"


def test_imported_functions_retain_definition_site_scope(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                secret: int = 7;
                export fn answer() -> int {
                    return secret;
                }
            """,
            "app.echo": """
                secret: int = 99;
                import answer from "math";
                say(answer());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "7")


def test_module_boundaries_prevent_accidental_name_leakage(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "left.echo": """
                helper: int = 1;
                export fn left_value() -> int {
                    return helper;
                }
            """,
            "right.echo": """
                export fn right_value() -> int {
                    return helper;
                }
            """,
            "app.echo": """
                import left_value from "left";
                import right_value from "right";
                say(left_value());
                say(right_value());
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "helper")
    assert "1" not in result.output.splitlines()
