from pathlib import Path

import pytest

from echo.errors import ModuleResolveError
from echo.modules.resolver import ModuleResolver
from echo.std import std_root
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_std_meta_import_from_install_tree(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import stdOk from "std/meta";
                import stdName from "std/meta";
                say(stdOk());
                say(stdName);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "true\necho-std")


def test_std_does_not_resolve_beside_importer(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "std/meta.echo": 'export fn stdOk() -> bool { return false; }',
            "app.echo": """
                import stdOk from "std/meta";
                say(stdOk());
            """,
        },
    )
    # Reserved std/… always hits the install tree, not a local std/ folder.
    assert_success(run_entry(tmp_path), "true")


def test_dot_slash_std_resolves_locally(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "std/meta.echo": 'export fn localOk() -> bool { return true; }',
            "app.echo": """
                import localOk from "./std/meta";
                say(localOk());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "true")


def test_bare_std_is_invalid() -> None:
    with pytest.raises(ModuleResolveError) as caught:
        ModuleResolver().validate_module_name("std")
    assert caught.value.code == "E3001"
    assert caught.value.help_text is not None
    assert "std/" in caught.value.help_text


def test_missing_std_module_names_std_root(tmp_path: Path) -> None:
    write_modules(tmp_path, {"app.echo": 'import x from "std/missing";'})
    result = run_entry(tmp_path)
    assert_echo_error(result, "E3002", "std/missing")
    assert "looked for" in result.output.lower()
    assert "echo std" in result.output.lower() or "std" in result.output.lower()


def test_std_root_override(tmp_path: Path) -> None:
    custom = tmp_path / "custom_std"
    custom.mkdir()
    (custom / "demo.echo").write_text(
        "export fn demo() -> int { return 9; }\n",
        encoding="utf-8",
    )
    resolver = ModuleResolver(std_root=custom)
    resolved = resolver.resolve(tmp_path / "app.echo", "std/demo")
    assert resolved == (custom / "demo.echo").resolve()


def test_default_std_root_contains_meta() -> None:
    meta = std_root() / "meta.echo"
    assert meta.is_file()
    assert ModuleResolver().resolve(Path("anywhere.echo"), "std/meta") == meta.resolve()


def test_same_std_module_is_one_identity(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "left.echo": """
                import stdName from "std/meta";
                export fn left() -> str { return stdName; }
            """,
            "right.echo": """
                import stdName from "std/meta";
                export fn right() -> str { return stdName; }
            """,
            "app.echo": """
                import left from "left";
                import right from "right";
                say(left());
                say(right());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "echo-std\necho-std")
