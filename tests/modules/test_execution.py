from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from echo.modules.loader import ModuleLoader
from echo.modules.records import INITIALIZED, NOT_INITIALIZED
from modules.harness import write_modules


def _path(root: Path, name: str) -> Path:
    return (root / name).resolve()


def _load(loader: ModuleLoader, entry: Path) -> tuple[object, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        module = loader.load(entry)
    return module, stdout.getvalue()


def test_dependencies_execute_before_importers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "constants.echo": 'say("constants");',
            "math.echo": 'say("math");',
            "app.echo": 'say("app");',
        },
    )
    loader = ModuleLoader()
    loader.declare_imports(_path(tmp_path, "math.echo"), ["constants"])
    loader.declare_imports(_path(tmp_path, "app.echo"), ["math"])
    _, output = _load(loader, _path(tmp_path, "app.echo"))
    assert output.strip() == "constants\nmath\napp"
    assert loader.initialized_paths() == [
        _path(tmp_path, "constants.echo"),
        _path(tmp_path, "math.echo"),
        _path(tmp_path, "app.echo"),
    ]


def test_entry_module_executes_last(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "dep.echo": 'say("dep");',
            "app.echo": 'say("entry");',
        },
    )
    loader = ModuleLoader()
    loader.declare_imports(_path(tmp_path, "app.echo"), ["dep"])
    _, output = _load(loader, _path(tmp_path, "app.echo"))
    assert output.strip() == "dep\nentry"
    assert loader.initialized_paths()[-1] == _path(tmp_path, "app.echo")


def test_a_module_executes_once_per_process(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": 'say("common");',
            "app.echo": 'say("app");',
        },
    )
    app = _path(tmp_path, "app.echo")
    common = _path(tmp_path, "common.echo")
    loader = ModuleLoader()
    loader.declare_imports(app, ["common", "common"])
    first, output = _load(loader, app)
    again, second_output = _load(loader, app)
    assert first is again
    assert loader.module(common) is loader.module(common)
    assert output.strip() == "common\napp"
    assert second_output == ""
    assert loader.initialized_paths().count(common) == 1


def test_shared_dependencies_execute_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "common.echo": 'say("common");',
            "a.echo": 'say("a");',
            "b.echo": 'say("b");',
            "app.echo": 'say("app");',
        },
    )
    loader = ModuleLoader()
    loader.declare_imports(_path(tmp_path, "a.echo"), ["common"])
    loader.declare_imports(_path(tmp_path, "b.echo"), ["common"])
    loader.declare_imports(_path(tmp_path, "app.echo"), ["a", "b"])
    _, output = _load(loader, _path(tmp_path, "app.echo"))
    lines = output.splitlines()
    assert lines.count("common") == 1
    assert lines.index("common") < lines.index("a")
    assert lines.index("common") < lines.index("b")
    assert lines[-1] == "app"


def test_diamond_dependency_orders_shared_module_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "a.echo": 'say("A");',
            "b.echo": 'say("B");',
            "c.echo": 'say("C");',
            "d.echo": 'say("D");',
        },
    )
    loader = ModuleLoader()
    loader.declare_imports(_path(tmp_path, "b.echo"), ["d"])
    loader.declare_imports(_path(tmp_path, "c.echo"), ["d"])
    loader.declare_imports(_path(tmp_path, "a.echo"), ["b", "c"])
    _, output = _load(loader, _path(tmp_path, "a.echo"))
    lines = output.splitlines()
    assert lines.count("D") == 1
    assert lines.index("D") < lines.index("B")
    assert lines.index("D") < lines.index("C")
    assert lines[-1] == "A"


def test_module_state_is_shared_across_importers(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "store.echo": 'say("store");',
            "writer.echo": 'say("writer");',
            "app.echo": 'say("app");',
        },
    )
    loader = ModuleLoader()
    loader.declare_imports(_path(tmp_path, "writer.echo"), ["store"])
    loader.declare_imports(_path(tmp_path, "app.echo"), ["writer", "store"])
    first, output = _load(loader, _path(tmp_path, "app.echo"))
    store = loader.module(_path(tmp_path, "store.echo"))
    assert store is not None
    assert first is loader.module(_path(tmp_path, "app.echo"))
    assert store.state == INITIALIZED
    assert output.splitlines().count("store") == 1


def test_top_level_code_executes_exactly_once(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "once.echo": 'say("once");',
            "first.echo": 'say("first");',
            "app.echo": 'say("app");',
        },
    )
    loader = ModuleLoader()
    loader.declare_imports(_path(tmp_path, "first.echo"), ["once"])
    loader.declare_imports(_path(tmp_path, "app.echo"), ["once", "first"])
    _, output = _load(loader, _path(tmp_path, "app.echo"))
    assert output.splitlines().count("once") == 1
    assert output.strip().endswith("app")


def test_failed_dependency_is_not_exposed_as_initialized(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "broken.echo": 'boom: int = "nope";',
            "app.echo": 'say("app");',
        },
    )
    loader = ModuleLoader()
    loader.declare_imports(_path(tmp_path, "app.echo"), ["broken"])
    stdout = StringIO()
    with redirect_stdout(stdout), pytest.raises(Exception):
        loader.load(_path(tmp_path, "app.echo"))
    assert "app" not in stdout.getvalue()
    broken = loader.module(_path(tmp_path, "broken.echo"))
    app = loader.module(_path(tmp_path, "app.echo"))
    assert broken is not None and broken.state != INITIALIZED
    assert app is not None and app.state == NOT_INITIALIZED
    assert loader.initialized_paths() == []
