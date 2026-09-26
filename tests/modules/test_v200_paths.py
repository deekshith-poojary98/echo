from pathlib import Path

import pytest

from echo.errors import ModuleResolveError
from echo.modules.resolver import ModuleResolver
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_bare_sibling_import_still_works(tmp_path: Path) -> None:
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


def test_dot_slash_sibling_import(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
            """,
            "app.echo": """
                import add from "./math";
                say(add(1, 4));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "5")


def test_nested_subdirectory_import(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "lib/math.echo": """
                export fn square(x: int) -> int {
                    return x * x;
                }
            """,
            "app.echo": """
                import square from "lib/math";
                say(square(6));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "36")


def test_dot_slash_nested_import(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "lib/util.echo": """
                export fn id(n: int) -> int {
                    return n;
                }
            """,
            "app.echo": """
                import id from "./lib/util";
                say(id(9));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "9")


def test_parent_directory_import(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "shared.echo": """
                export fn answer() -> int {
                    return 42;
                }
            """,
            "pkg/app.echo": """
                import answer from "../shared";
                say(answer());
            """,
        },
    )
    assert_success(run_entry(tmp_path, "pkg/app.echo"), "42")


def test_nested_modules_can_import_each_other(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "lib/core.echo": """
                export fn ten() -> int {
                    return 10;
                }
            """,
            "lib/more.echo": """
                import ten from "./core";
                export fn twenty() -> int {
                    return ten() + ten();
                }
            """,
            "app.echo": """
                import twenty from "lib/more";
                say(twenty());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "20")


def test_same_file_via_bare_and_dot_slash_is_one_module(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "once.echo": 'say("once"); export x: int = 7;',
            "left.echo": 'import x from "once"; export fn left() -> int { return x; }',
            "right.echo": 'import x from "./once"; export fn right() -> int { return x; }',
            "app.echo": """
                import left from "left";
                import right from "right";
                say(left());
                say(right());
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_success(result, "once\n7\n7")
    assert result.output.count("once") == 1


def test_missing_nested_module_is_echo_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": 'import missing from "lib/nope";',
        },
    )
    assert_echo_error(run_entry(tmp_path), "E3002", "lib/nope")


def test_explicit_echo_suffix_is_invalid(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": "export x: int = 1;",
            "app.echo": 'import x from "math.echo";',
        },
    )
    assert_echo_error(run_entry(tmp_path), "E3001")


def test_absolute_specifier_is_invalid() -> None:
    resolver = ModuleResolver()
    with pytest.raises(ModuleResolveError) as caught:
        resolver.validate_module_name("/tmp/math")
    assert caught.value.code == "E3001"


def test_mid_path_dotdot_is_invalid() -> None:
    resolver = ModuleResolver()
    with pytest.raises(ModuleResolveError) as caught:
        resolver.validate_module_name("lib/../math")
    assert caught.value.code == "E3001"


def test_resolver_nested_path_unit(tmp_path: Path) -> None:
    write_modules(tmp_path, {"lib/math.echo": "export x: int = 1;", "app.echo": "say(1);"})
    resolver = ModuleResolver()
    app = tmp_path / "app.echo"
    path = resolver.resolve(app, "lib/math")
    assert path == (tmp_path / "lib" / "math.echo").resolve()
    assert resolver.resolve(app, "./lib/math") == path
