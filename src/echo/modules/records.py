from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from echo.frontend.ast.nodes import Program
from echo.runtime.context import Environment

NOT_INITIALIZED = "not_initialized"
INITIALIZING = "initializing"
INITIALIZED = "initialized"
FAILED = "failed"


@dataclass
class Module:
    path: Path
    source: str
    ast: Program
    dependencies: list[Path] = field(default_factory=list)
    imported_bindings: list[tuple[str, Path]] = field(default_factory=list)
    specifiers: dict[str, Path] = field(default_factory=dict)
    exports: set[str] = field(default_factory=set)
    env: Environment | None = None
    discovered: bool = False
    state: str = NOT_INITIALIZED
