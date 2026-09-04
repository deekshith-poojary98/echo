from pathlib import Path

import pytest

from echo.errors import EchoError, ModuleGraphError
from echo.modules.graph import ModuleGraph
from modules.harness import write_modules


def _path(root: Path, name: str) -> Path:
    return (root / name).resolve()


def _assert_cycle(graph: ModuleGraph, *names: str) -> None:
    with pytest.raises(ModuleGraphError) as caught:
        graph.detect_cycles()
    assert isinstance(caught.value, EchoError)
    assert caught.value.code == "E3003"
    text = caught.value.message.lower()
    assert any(name in text for name in names)


def test_direct_cycle_is_rejected(tmp_path: Path) -> None:
    write_modules(tmp_path, {"a.echo": "x: int = 1;", "b.echo": "x: int = 1;"})
    graph = ModuleGraph()
    graph.add_dependency(_path(tmp_path, "a.echo"), _path(tmp_path, "b.echo"))
    graph.add_dependency(_path(tmp_path, "b.echo"), _path(tmp_path, "a.echo"))
    _assert_cycle(graph, "a.echo", "b.echo")
    with pytest.raises(ModuleGraphError):
        graph.dependency_order(_path(tmp_path, "a.echo"))


def test_indirect_cycle_is_rejected(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {"a.echo": "x: int = 1;", "b.echo": "x: int = 1;", "c.echo": "x: int = 1;"},
    )
    graph = ModuleGraph()
    graph.add_dependency(_path(tmp_path, "a.echo"), _path(tmp_path, "b.echo"))
    graph.add_dependency(_path(tmp_path, "b.echo"), _path(tmp_path, "c.echo"))
    graph.add_dependency(_path(tmp_path, "c.echo"), _path(tmp_path, "a.echo"))
    _assert_cycle(graph, "a.echo", "b.echo", "c.echo")


def test_longer_dependency_cycle_is_rejected(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "one.echo": "x: int = 1;",
            "two.echo": "x: int = 1;",
            "three.echo": "x: int = 1;",
            "four.echo": "x: int = 1;",
        },
    )
    graph = ModuleGraph()
    graph.add_dependency(_path(tmp_path, "one.echo"), _path(tmp_path, "two.echo"))
    graph.add_dependency(_path(tmp_path, "two.echo"), _path(tmp_path, "three.echo"))
    graph.add_dependency(_path(tmp_path, "three.echo"), _path(tmp_path, "four.echo"))
    graph.add_dependency(_path(tmp_path, "four.echo"), _path(tmp_path, "one.echo"))
    _assert_cycle(graph, "one.echo", "two.echo", "three.echo", "four.echo")


def test_no_partially_initialized_module_is_exposed(tmp_path: Path) -> None:
    write_modules(tmp_path, {"a.echo": "x: int = 1;", "b.echo": "x: int = 1;"})
    graph = ModuleGraph()
    graph.add_dependency(_path(tmp_path, "a.echo"), _path(tmp_path, "b.echo"))
    graph.add_dependency(_path(tmp_path, "b.echo"), _path(tmp_path, "a.echo"))
    with pytest.raises(ModuleGraphError):
        graph.dependency_order(_path(tmp_path, "a.echo"))


def test_cycle_error_identifies_the_dependency_problem(tmp_path: Path) -> None:
    write_modules(tmp_path, {"alpha.echo": "x: int = 1;", "beta.echo": "x: int = 1;"})
    graph = ModuleGraph()
    graph.add_dependency(_path(tmp_path, "alpha.echo"), _path(tmp_path, "beta.echo"))
    graph.add_dependency(_path(tmp_path, "beta.echo"), _path(tmp_path, "alpha.echo"))
    with pytest.raises(ModuleGraphError) as caught:
        graph.detect_cycles()
    text = caught.value.message.lower()
    assert "alpha" in text or "beta" in text
