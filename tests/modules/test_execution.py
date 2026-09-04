from pathlib import Path

from modules.harness import assert_success, run_entry, write_modules


def test_dependencies_execute_before_importers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "constants.echo": """
                export n: int = 1;
                say("constants");
            """,
            "math.echo": """
                import n from "constants";
                export fn id(x: int) -> int {
                    return x;
                }
                say("math");
            """,
            "app.echo": """
                import id from "math";
                say("app");
                say(id(1));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "constants\nmath\napp\n1")


def test_entry_module_executes_last(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "dep.echo": """
                export ready: int = 1;
                say("dep");
            """,
            "app.echo": """
                import ready from "dep";
                say("entry");
            """,
        },
    )
    assert_success(run_entry(tmp_path), "dep\nentry")


def test_a_module_executes_once_per_process(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": """
                export hits: list = [];
                export label: str = "ok";
                say("common");
            """,
            "app.echo": """
                import hits from "common";
                import label from "common";
                say(label);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "common\nok")


def test_shared_dependencies_execute_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": """
                export label: str = "shared";
                say("common");
            """,
            "a.echo": """
                import label from "common";
                export fn from_a() -> str {
                    return label;
                }
            """,
            "b.echo": """
                import label from "common";
                export fn from_b() -> str {
                    return label;
                }
            """,
            "app.echo": """
                import from_a from "a";
                import from_b from "b";
                say(from_a());
                say(from_b());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "common\nshared\nshared")


def test_module_state_is_shared_across_importers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "store.echo": """
                export items: list = [];
            """,
            "writer.echo": """
                import items from "store";
                export fn add(value: int) {
                    items.push(value);
                }
            """,
            "app.echo": """
                import add from "writer";
                import items from "store";
                add(1);
                add(2);
                say(items);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "[1, 2]")


def test_top_level_code_executes_exactly_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "once.echo": """
                export n: int = 1;
                say("once");
            """,
            "first.echo": """
                import n from "once";
                export fn read() -> int {
                    return n;
                }
            """,
            "app.echo": """
                import n from "once";
                import read from "first";
                say(read());
                say(n);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "once\n1\n1")
