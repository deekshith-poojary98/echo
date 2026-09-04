from pathlib import Path

from echo.modules.graph import ModuleGraph
from modules.harness import write_modules


def _path(root: Path, name: str) -> Path:
    return (root / name).resolve()


def test_dependencies_execute_before_importers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "constants.echo": "x: int = 1;",
            "math.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    graph = ModuleGraph()
    graph.add_dependency(_path(tmp_path, "math.echo"), _path(tmp_path, "constants.echo"))
    graph.add_dependency(_path(tmp_path, "app.echo"), _path(tmp_path, "math.echo"))
    assert graph.dependency_order(_path(tmp_path, "app.echo")) == [
        _path(tmp_path, "constants.echo"),
        _path(tmp_path, "math.echo"),
        _path(tmp_path, "app.echo"),
    ]


def test_entry_module_executes_last(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "dep.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    graph = ModuleGraph()
    graph.add_dependency(_path(tmp_path, "app.echo"), _path(tmp_path, "dep.echo"))
    order = graph.dependency_order(_path(tmp_path, "app.echo"))
    assert order == [_path(tmp_path, "dep.echo"), _path(tmp_path, "app.echo")]


def test_a_module_executes_once_per_process(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    app = _path(tmp_path, "app.echo")
    common = _path(tmp_path, "common.echo")
    graph = ModuleGraph()
    graph.add_dependency(app, common)
    graph.add_dependency(app, common)
    assert graph.modules().count(common) == 1
    assert graph.dependency_order(app) == [common, app]


def test_shared_dependencies_execute_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": "x: int = 1;",
            "a.echo": "x: int = 1;",
            "b.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    app = _path(tmp_path, "app.echo")
    a = _path(tmp_path, "a.echo")
    b = _path(tmp_path, "b.echo")
    common = _path(tmp_path, "common.echo")
    graph = ModuleGraph()
    graph.add_dependency(app, a)
    graph.add_dependency(app, b)
    graph.add_dependency(a, common)
    graph.add_dependency(b, common)
    order = graph.dependency_order(app)
    assert order.count(common) == 1
    assert order.index(common) < order.index(a)
    assert order.index(common) < order.index(b)
    assert order[-1] == app


def test_diamond_dependency_orders_shared_module_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "a.echo": "x: int = 1;",
            "b.echo": "x: int = 1;",
            "c.echo": "x: int = 1;",
            "d.echo": "x: int = 1;",
        },
    )
    a = _path(tmp_path, "a.echo")
    b = _path(tmp_path, "b.echo")
    c = _path(tmp_path, "c.echo")
    d = _path(tmp_path, "d.echo")
    graph = ModuleGraph()
    graph.add_dependency(a, b)
    graph.add_dependency(a, c)
    graph.add_dependency(b, d)
    graph.add_dependency(c, d)
    order = graph.dependency_order(a)
    assert order.count(d) == 1
    assert order.index(d) < order.index(b)
    assert order.index(d) < order.index(c)
    assert order[-1] == a


def test_module_state_is_shared_across_importers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "store.echo": "x: int = 1;",
            "writer.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    app = _path(tmp_path, "app.echo")
    writer = _path(tmp_path, "writer.echo")
    store = _path(tmp_path, "store.echo")
    graph = ModuleGraph()
    graph.add_dependency(writer, store)
    graph.add_dependency(app, writer)
    graph.add_dependency(app, store)
    order = graph.dependency_order(app)
    assert order.count(store) == 1
    assert order.index(store) < order.index(writer)
    assert order[-1] == app


def test_top_level_code_executes_exactly_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "once.echo": "x: int = 1;",
            "first.echo": "x: int = 1;",
            "app.echo": "x: int = 1;",
        },
    )
    app = _path(tmp_path, "app.echo")
    first = _path(tmp_path, "first.echo")
    once = _path(tmp_path, "once.echo")
    graph = ModuleGraph()
    graph.add_dependency(first, once)
    graph.add_dependency(app, once)
    graph.add_dependency(app, first)
    order = graph.dependency_order(app)
    assert order.count(once) == 1
    assert order.index(once) < order.index(first)
    assert order[-1] == app
