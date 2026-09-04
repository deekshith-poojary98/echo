from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from echo.frontend.ast.nodes import Program

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
    state: str = NOT_INITIALIZED
