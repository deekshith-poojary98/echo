"""Echo install-tree standard modules (`import … from "std/…"`)."""

from __future__ import annotations

from pathlib import Path

from echo.frontend.ast.nodes import ExportDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.runtime.host import resolve_filesystem_path


def std_root() -> Path:
    """Directory that backs the reserved `std/…` import prefix."""
    return Path(__file__).resolve().parent


def resolve_std_root(root: str | Path | None = None) -> Path:
    """Resolve the std tree (explicit path, else `ECHO_STD_ROOT`, else install tree)."""
    import os

    if root is not None:
        candidate = Path(root).expanduser()
    else:
        env = os.environ.get("ECHO_STD_ROOT")
        if not env:
            return std_root()
        candidate = Path(env).expanduser()
    try:
        return resolve_filesystem_path(candidate)
    except OSError as exc:
        # Path.resolve() raises RuntimeError/OSError on symlink cycles; CLI /
        # ModuleResolver construction used to leak that traceback.
        raise OSError(f"cannot resolve std root: {candidate}") from exc


def list_std_module_paths(root: str | Path | None = None) -> list[Path]:
    """Sorted `.echo` files under the std root (recursive)."""
    base = resolve_std_root(root)
    if not base.is_dir():
        return []
    return sorted(path for path in base.rglob("*.echo") if path.is_file())


def list_std_modules(root: str | Path | None = None) -> list[str]:
    """Import specifiers such as `std/math`, `std/http`."""
    base = resolve_std_root(root)
    modules: list[str] = []
    for path in list_std_module_paths(base):
        rel = path.relative_to(base).with_suffix("").as_posix()
        modules.append(f"std/{rel}")
    return modules


def list_std_exports(path: Path) -> list[str]:
    """Export names declared in a std module file (parse-only)."""
    source = path.read_text(encoding="utf-8")
    tokens = Lexer().tokenize(source, filename=str(path))
    program = Parser(tokens).parse()
    names: list[str] = []
    for statement in program.statements:
        if isinstance(statement, ExportDeclaration):
            names.append(statement.name)
    return sorted(names)


def list_std_inventory(root: str | Path | None = None) -> list[tuple[str, Path, list[str]]]:
    """`(specifier, path, exports)` for each std module."""
    base = resolve_std_root(root)
    rows: list[tuple[str, Path, list[str]]] = []
    for path in list_std_module_paths(base):
        rel = path.relative_to(base).with_suffix("").as_posix()
        rows.append((f"std/{rel}", path, list_std_exports(path)))
    return rows
