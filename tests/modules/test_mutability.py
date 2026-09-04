from pathlib import Path

from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_imported_bindings_cannot_be_rebound(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "config.echo": """
                export value: int = 10;
            """,
            "app.echo": """
                import value from "config";
                value = 11;
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "value")


def test_use_mut_cannot_cross_a_module_boundary(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "config.echo": """
                export value: int = 10;
            """,
            "app.echo": """
                import value from "config";
                fn bump() {
                    use mut value;
                    value = value + 1;
                }
                bump();
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "value")


def test_imported_lists_share_collection_identity(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export values: list = [1, 2, 3];
            """,
            "app.echo": """
                import values from "data";
                values.push(4);
                say(values);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "[1, 2, 3, 4]")


def test_imported_hashes_share_collection_identity(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export table: hash = {"a": 1};
            """,
            "app.echo": """
                import table from "data";
                table["b"] = 2;
                say(table);
            """,
        },
    )
    result = run_entry(tmp_path)
    assert result.exit_code == 0, result.output
    assert "a" in result.output
    assert "1" in result.output
    assert "b" in result.output
    assert "2" in result.output


def test_mutating_an_imported_collection_is_visible_to_other_references(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export values: list = [1];
                export fn snapshot() -> list {
                    return values;
                }
            """,
            "app.echo": """
                import values from "data";
                import snapshot from "data";
                values.push(2);
                say(snapshot());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "[1, 2]")


def test_rebinding_an_imported_collection_is_rejected(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export values: list = [1, 2, 3];
            """,
            "app.echo": """
                import values from "data";
                values = [9, 9];
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "values")
