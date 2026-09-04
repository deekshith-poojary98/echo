from pathlib import Path

from echo.modules.loader import ModuleLoader
from echo.runtime.functions import EchoFunction
from helpers import run_echo
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def _path(root: Path, name: str) -> Path:
    return (root / name).resolve()


def _load(root: Path, entry: str = "app.echo") -> ModuleLoader:
    loader = ModuleLoader()
    loader.load(_path(root, entry))
    return loader


def test_module_scope(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                secret: int = 1;
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
            """,
            "app.echo": """
                import add from "math";
                label: str = "app";
            """,
        },
    )
    loader = _load(tmp_path)
    math = loader.module(_path(tmp_path, "math.echo"))
    app = loader.module(_path(tmp_path, "app.echo"))
    assert math is not None and app is not None
    assert math.env is not None and app.env is not None
    assert math.env is not app.env
    assert "secret" in math.env.values
    assert "secret" not in app.env.values
    assert "label" in app.env.values
    assert "label" not in math.env.values
    assert isinstance(app.env.resolve_function("add"), EchoFunction)


def test_dependency_execution_order(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "constants.echo": """
                export n: int = 1;
                say("constants");
            """,
            "math.echo": """
                import n from "constants";
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                say("math");
            """,
            "app.echo": """
                import add from "math";
                say("app");
            """,
        },
    )
    assert_success(run_entry(tmp_path), "constants\nmath\napp")


def test_execute_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": """
                export n: int = 1;
                say("common");
            """,
            "app.echo": """
                import n from "common";
                say("app");
            """,
        },
    )
    loader = ModuleLoader()
    entry = _path(tmp_path, "app.echo")
    loader.load(entry)
    loader.load(entry)
    assert loader.initialized_paths().count(_path(tmp_path, "common.echo")) == 1


def test_imported_function_callable(tmp_path: Path) -> None:
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


def test_imported_variable_readable(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "config.echo": """
                export x: int = 10;
            """,
            "app.echo": """
                import x from "config";
                say(x);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "10")


def test_imported_collection_shared(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export items: list = [1, 2, 3];
            """,
            "app.echo": """
                import items from "data";
                items.push(4);
            """,
        },
    )
    loader = _load(tmp_path)
    data = loader.module(_path(tmp_path, "data.echo"))
    app = loader.module(_path(tmp_path, "app.echo"))
    assert data is not None and app is not None
    assert data.env is not None and app.env is not None
    assert app.env.values["items"] is data.env.values["items"]
    assert data.env.values["items"] == [1, 2, 3, 4]


def test_imported_binding_cannot_rebind(tmp_path: Path) -> None:
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
                add = 1;
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "add")


def test_imported_binding_cannot_use_mut(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "other.echo": """
                export count: int = 0;
            """,
            "app.echo": """
                import count from "other";
                fn foo() {
                    use mut count;
                }
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "count")


def test_export_does_not_execute_as_statement() -> None:
    result = run_echo(
        """
        export fn add(a: int, b: int) -> int {
            return a + b;
        }
        say(add(2, 3));
        """
    )
    assert_success(result, "5")


def test_private_name_not_bound_to_importer(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                hidden: int = 7;
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
            """,
            "app.echo": """
                import add from "math";
                say(hidden);
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "hidden")
    assert not any(line.strip() == "7" for line in result.output.splitlines())


def test_chain_a_b_c(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "c.echo": """
                export n: int = 3;
                say("C");
            """,
            "b.echo": """
                import n from "c";
                export fn plus(x: int) -> int {
                    return x + n;
                }
                say("B");
            """,
            "a.echo": """
                import plus from "b";
                say("A");
                say(plus(4));
            """,
        },
    )
    assert_success(run_entry(tmp_path, "a.echo"), "C\nB\nA\n7")


def test_diamond_imports_share_one_module(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": """
                export box: list = [];
                export fn push_box(value: str) {
                    use mut box;
                    box.push(value);
                }
                say("common");
            """,
            "left.echo": """
                import push_box from "common";
                export fn left_push() {
                    push_box("L");
                }
            """,
            "right.echo": """
                import push_box from "common";
                export fn right_push() {
                    push_box("R");
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
