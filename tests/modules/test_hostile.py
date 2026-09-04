from pathlib import Path

from helpers import assert_no_python_leak
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_hostile_chain_with_closure_collection_and_private_names(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "c.echo": """
                secret: int = 10;
                export fn close_over() -> int {
                    return secret;
                }
            """,
            "b.echo": """
                import close_over from "c";
                hidden: int = 99;
                export box: list = [];
                export fn from_c() -> int {
                    return close_over();
                }
                export fn push_box(value: str) {
                    use mut box;
                    box.push(value);
                }
            """,
            "a.echo": """
                import from_c from "b";
                import box from "b";
                import push_box from "b";
                hidden: int = 1;
                fn wrap() -> int {
                    fn inner() -> int {
                        return from_c() + hidden;
                    }
                    return inner();
                }
                push_box("x");
                say(wrap());
                say(box);
            """,
        },
    )
    result = run_entry(tmp_path, "a.echo")
    assert_success(result, '11\n["x"]')
    assert_no_python_leak(result)


def test_hostile_diamond_plus_same_module_use_mut(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": """
                export n: int = 2;
                export items: list = [];
                export fn add_item(value: int) {
                    use mut items;
                    items.push(value);
                }
            """,
            "left.echo": """
                import n from "common";
                import add_item from "common";
                export fn left_add() {
                    add_item(n);
                }
            """,
            "right.echo": """
                import add_item from "common";
                export fn right_add() {
                    add_item(3);
                }
            """,
            "app.echo": """
                import left_add from "left";
                import right_add from "right";
                import items from "common";
                left_add();
                right_add();
                items.push(4);
                say(items);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "[2, 3, 4]")


def test_hostile_duplicate_import_and_local_collision_are_errors(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "one.echo": "export x: int = 1;",
            "two.echo": "export x: int = 2;",
            "app.echo": """
                import x from "one";
                import x from "two";
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "x")
    assert_no_python_leak(result)


def test_hostile_rebind_imported_collection_is_rejected(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": "export items: list = [1];",
            "app.echo": """
                import items from "data";
                items = [9];
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "items")
    assert_no_python_leak(result)


def test_hostile_use_mut_on_import_is_rejected_even_in_nested_function(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "other.echo": "export count: int = 0;",
            "app.echo": """
                import count from "other";
                fn outer() {
                    fn inner() {
                        use mut count;
                    }
                }
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "count")
    assert_no_python_leak(result)


def test_hostile_failed_dependency_does_not_run_importer(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "broken.echo": """
                say("broken");
                boom: int = "nope";
                export ready: int = 1;
            """,
            "mid.echo": """
                import ready from "broken";
                export ok: int = ready;
                say("mid");
            """,
            "app.echo": """
                import ok from "mid";
                say("app");
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result)
    assert "mid" not in result.output
    assert "app" not in result.output
    assert_no_python_leak(result)


def test_hostile_private_name_does_not_leak_through_nested_imports(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "c.echo": """
                locked: int = 7;
                export fn read() -> int {
                    return locked;
                }
            """,
            "b.echo": """
                import read from "c";
                export fn proxy() -> int {
                    return read();
                }
            """,
            "app.echo": """
                import proxy from "b";
                say(proxy());
                say(locked);
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "locked")
    assert not any(line.strip() == "7" for line in result.output.splitlines())
    assert_no_python_leak(result)


def test_hostile_same_module_use_mut_still_works_beside_imports(tmp_path: Path) -> None:
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
                total: int = 0;
                fn bump() {
                    use mut total;
                    total = add(total, 1);
                }
                bump();
                bump();
                say(total);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "2")


def test_hostile_model_a_defining_module_needs_use_mut(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export items: list = [];
                export fn push_item(value: int) {
                    use mut items;
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
