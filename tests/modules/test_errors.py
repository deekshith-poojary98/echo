from pathlib import Path

from helpers import assert_no_python_leak
from modules.harness import assert_echo_error, run_entry, write_modules


def test_missing_module_produces_an_echo_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import add from "missing";
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "missing")
    assert_no_python_leak(result)


def test_missing_export_produces_an_echo_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
            """,
            "app.echo": """
                import absent from "math";
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "absent")
    assert_no_python_leak(result)


def test_invalid_import_produces_an_echo_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
            """,
            "app.echo": """
                import from "math";
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result)
    assert_no_python_leak(result)


def test_import_collision_produces_an_echo_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export x: int = 1;
            """,
            "app.echo": """
                x: int = 10;
                import x from "math";
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "x")
    assert_no_python_leak(result)


def test_duplicate_import_of_same_name_is_a_collision(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export x: int = 1;
            """,
            "other.echo": """
                export x: int = 2;
            """,
            "app.echo": """
                import x from "math";
                import x from "other";
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "x")
    assert_no_python_leak(result)


def test_circular_dependency_produces_an_echo_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "a.echo": """
                import bval from "b";
                export aval: int = 1;
            """,
            "b.echo": """
                import aval from "a";
                export bval: int = 2;
            """,
            "app.echo": """
                import aval from "a";
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result)
    assert_no_python_leak(result)


def test_python_exceptions_do_not_leak(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "broken.echo": """
                export fn boom() -> int {
                    return 1 / 0;
                }
            """,
            "app.echo": """
                import boom from "broken";
                say(boom());
            """,
        },
    )
    result = run_entry(tmp_path)
    assert result.exit_code == 1, result.output
    assert_no_python_leak(result)
    assert "ZeroDivisionError" not in result.output
    assert "Traceback" not in result.output
