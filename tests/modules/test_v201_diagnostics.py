from pathlib import Path

import pytest

from echo.errors import ModuleGraphError, ModuleResolveError
from echo.modules.graph import ModuleGraph
from echo.modules.resolver import ModuleResolver
from modules.harness import assert_echo_error, run_entry, write_modules


def test_missing_nested_module_names_looked_for_path(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": 'import missing from "lib/nope";',
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "E3002", "lib/nope")
    assert "looked for" in result.output.lower()
    assert "lib/nope.echo" in result.output


def test_missing_module_error_points_at_import(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": 'import missing from "absent";',
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "E3002", "absent")
    assert "-->" in result.output
    assert "app.echo" in result.output


def test_echo_suffix_help_text() -> None:
    with pytest.raises(ModuleResolveError) as caught:
        ModuleResolver().validate_module_name("math.echo")
    assert caught.value.code == "E3001"
    assert caught.value.help_text is not None
    assert ".echo" in caught.value.help_text


def test_mid_path_dotdot_help_text() -> None:
    with pytest.raises(ModuleResolveError) as caught:
        ModuleResolver().validate_module_name("lib/../math")
    assert caught.value.code == "E3001"
    assert caught.value.help_text is not None
    assert ".." in caught.value.help_text


def test_absolute_specifier_help_text() -> None:
    with pytest.raises(ModuleResolveError) as caught:
        ModuleResolver().validate_module_name("/tmp/math")
    assert caught.value.code == "E3001"
    assert caught.value.help_text is not None
    assert "relative" in caught.value.help_text.lower()


def test_nested_same_basename_cycle_labels_are_distinct(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "lib/a.echo": "x: int = 1;",
            "pkg/a.echo": "x: int = 1;",
        },
    )
    graph = ModuleGraph()
    left = (tmp_path / "lib" / "a.echo").resolve()
    right = (tmp_path / "pkg" / "a.echo").resolve()
    graph.add_dependency(left, right)
    graph.add_dependency(right, left)
    with pytest.raises(ModuleGraphError) as caught:
        graph.detect_cycles()
    assert caught.value.code == "E3003"
    text = caught.value.message
    assert "lib/a.echo" in text
    assert "pkg/a.echo" in text
    assert "a.echo -> a.echo" not in text


def test_nested_path_cycle_through_imports(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "lib/left.echo": """
                import right from "../pkg/right";
                export left: int = 1;
            """,
            "pkg/right.echo": """
                import left from "../lib/left";
                export right: int = 2;
            """,
            "app.echo": 'import left from "lib/left";',
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "E3003")
    lower = result.output.lower()
    assert "circular" in lower
    assert "lib/left.echo" in lower or "pkg/right.echo" in lower