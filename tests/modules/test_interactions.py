from pathlib import Path

import pytest

from helpers import run_echo
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules

_MODEL_B_WITHOUT_USE_MUT = (
    "Model B interaction case: defining-module collection mutation without "
    "`use mut`. v0.3 is frozen on Model A. See docs/module-semantics.md §8.1."
)


def test_imported_function_plus_closure(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add_with_capture(x: int) -> int {
                    n: int = 5;
                    fn inner() -> int {
                        return x + n;
                    }
                    return inner();
                }
            """,
            "app.echo": """
                import add_with_capture from "math";
                say(add_with_capture(3));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "8")


def test_imported_function_plus_nested_function(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn outer(n: int) -> int {
                    fn inner() -> int {
                        return n + 1;
                    }
                    return inner();
                }
            """,
            "app.echo": """
                import outer from "math";
                say(outer(4));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "5")


def test_imported_function_plus_use(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                base: int = 10;
                export fn read() -> int {
                    use base;
                    return base;
                }
            """,
            "app.echo": """
                import read from "math";
                say(read());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "10")


def test_imported_function_plus_use_mut(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "counter.echo": """
                n: int = 0;
                export fn bump() {
                    use mut n;
                    n = n + 1;
                }
                export fn value() -> int {
                    return n;
                }
            """,
            "app.echo": """
                import bump from "counter";
                import value from "counter";
                bump();
                bump();
                say(value());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "2")


@pytest.mark.xfail(strict=True, reason=_MODEL_B_WITHOUT_USE_MUT)
def test_imported_mutable_list_plus_function_mutation(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export items: list = [];
                export fn push_item(value: int) {
                    items.push(value);
                }
            """,
            "app.echo": """
                import items from "data";
                import push_item from "data";
                push_item(1);
                items.push(2);
                say(items);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "[1, 2]")


@pytest.mark.xfail(strict=True, reason=_MODEL_B_WITHOUT_USE_MUT)
def test_imported_mutable_hash_plus_function_mutation(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export table: hash = {};
                export fn put(key: str, value: int) {
                    table[key] = value;
                }
            """,
            "app.echo": """
                import table from "data";
                import put from "data";
                put("a", 1);
                table["b"] = 2;
                say(table["a"]);
                say(table["b"]);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "1\n2")


def test_multiple_importers_sharing_one_mutable_export(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "store.echo": """
                export items: list = [];
            """,
            "one.echo": """
                import items from "store";
                export fn add_one() {
                    items.push(1);
                }
            """,
            "two.echo": """
                import items from "store";
                export fn add_two() {
                    items.push(2);
                }
            """,
            "app.echo": """
                import add_one from "one";
                import add_two from "two";
                import items from "store";
                add_one();
                add_two();
                say(items);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "[1, 2]")


def test_nested_dependency_plus_closure(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "constants.echo": """
                export offset: int = 10;
            """,
            "math.echo": """
                import offset from "constants";
                export fn add_offset(x: int) -> int {
                    fn inner() -> int {
                        return x + offset;
                    }
                    return inner();
                }
            """,
            "app.echo": """
                import add_offset from "math";
                say(add_offset(5));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "15")


def test_shared_dependency_imported_through_two_branches(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": """
                export box: list = [];
                say("common");
            """,
            "left.echo": """
                import box from "common";
                export fn left_push() {
                    box.push("L");
                }
            """,
            "right.echo": """
                import box from "common";
                export fn right_push() {
                    box.push("R");
                }
            """,
            "app.echo": """
                import left_push from "left";
                import right_push from "right";
                import box from "common";
                left_push();
                right_push();
                say(box);
            """,
        },
    )
    assert_success(run_entry(tmp_path), 'common\n["L", "R"]')


def test_private_module_state_captured_by_an_exported_function(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "hidden.echo": """
                secret: int = 3;
                export fn triple(x: int) -> int {
                    return x * secret;
                }
            """,
            "app.echo": """
                import triple from "hidden";
                say(triple(4));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "12")


def test_module_initialization_failure(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "broken.echo": """
                say("broken-started");
                boom: int = "nope";
                export ready: int = 1;
            """,
            "app.echo": """
                import ready from "broken";
                say("app-ran");
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result)
    assert "app-ran" not in result.output


def test_import_collision_after_local_declaration(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export x: int = 1;
            """,
            "app.echo": """
                x: int = 10;
                import x from "math";
                say(x);
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "x")


def test_imported_name_shadowing_inside_a_function(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export x: int = 1;
            """,
            "app.echo": """
                import x from "math";
                fn wrap() {
                    x: int = 9;
                    say(x);
                }
                wrap();
                say(x);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "9\n1")


def test_attempted_cross_module_use_mut(tmp_path: Path) -> None:
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
                    value = 11;
                }
                bump();
                say(value);
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "value")
    assert "11" not in result.lines


def test_same_module_use_mut_still_works_without_imports() -> None:
    result = run_echo(
        """
value: int = 10;
fn bump() {
    use mut value;
    value = 11;
}
bump();
say(value);
"""
    )
    assert_success(result, "11")
