from pathlib import Path

import pytest

from echo.errors import EchoError, ModuleResolveError
from echo.modules.resolver import ModuleResolver
from modules.harness import assert_success, run_entry, write_modules

# Specifiers passed to ModuleResolver are only the v0.3 bare name, e.g. "math",
# except for the explicit invalid-specifier cases below.


def _resolve(importer: Path, name: str) -> Path:
    return ModuleResolver().resolve(importer, name)


def test_every_echo_file_is_a_module(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                x: int = 10;
                say("math-module");
            """,
            "app.echo": """
                say("entry-module");
            """,
        },
    )
    result = run_entry(tmp_path, "app.echo")
    assert_success(result, "entry-module")
    other = run_entry(tmp_path, "math.echo")
    assert_success(other, "math-module")


def test_cli_file_is_the_entry_module(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "first.echo": 'say("first");',
            "second.echo": 'say("second");',
        },
    )
    assert_success(run_entry(tmp_path, "first.echo"), "first")
    assert_success(run_entry(tmp_path, "second.echo"), "second")


def test_echo_extension_is_implied(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    resolved = _resolve(tmp_path / "app.echo", "math")
    assert resolved == (tmp_path / "math.echo").resolve()


def test_relative_imports_resolve_beside_the_importer(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "nested/math.echo": "x: int = 1;",
            "math.echo": "x: int = 1;",
            "nested/app.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    assert _resolve(tmp_path / "app.echo", "math") == (tmp_path / "math.echo").resolve()
    assert _resolve(tmp_path / "nested/app.echo", "math") == (tmp_path / "nested/math.echo").resolve()


def test_missing_sibling_is_not_found_in_another_directory(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "lib/math.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    with pytest.raises(ModuleResolveError) as caught:
        _resolve(tmp_path / "app.echo", "math")
    assert isinstance(caught.value, EchoError)
    assert caught.value.code == "E3002"
    assert "math" in caught.value.message


def test_resolved_absolute_path_defines_module_identity(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": "x: int = 1;",
            "left.echo": "x: int = 1;",
            "right.echo": "x: int = 1;",
        },
    )
    from_left = _resolve(tmp_path / "left.echo", "common")
    from_right = _resolve(tmp_path / "right.echo", "common")
    assert from_left == from_right
    assert from_left == (tmp_path / "common.echo").resolve()
    assert from_left.is_absolute()


def test_equivalent_paths_resolve_to_one_module_identity(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "data.echo": "x: int = 1;",
            "via_name.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    via_name = _resolve(tmp_path / "via_name.echo", "data")
    via_app = _resolve(tmp_path / "app.echo", "data")
    assert via_name == via_app == (tmp_path / "data.echo").resolve()


def test_missing_module_is_not_found(tmp_path: Path) -> None:
    write_modules(tmp_path, {"app.echo": "x: int = 1;"})
    with pytest.raises(ModuleResolveError) as caught:
        _resolve(tmp_path / "app.echo", "missing")
    assert isinstance(caught.value, EchoError)
    assert caught.value.code == "E3002"
    assert "missing" in caught.value.message


@pytest.mark.parametrize(
    "specifier",
    ("math.echo", "./math", "../math", "lib/math"),
)
def test_alternate_specifier_is_invalid(tmp_path: Path, specifier: str) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": "x: int = 1;",
            "lib/math.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    with pytest.raises(ModuleResolveError) as caught:
        _resolve(tmp_path / "app.echo", specifier)
    assert isinstance(caught.value, EchoError)
    assert caught.value.code == "E3001"
    assert specifier in caught.value.message
