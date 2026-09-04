from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from echo.errors import SourceLocation
from echo.frontend.ast.nodes import TypeAnnotation


class SymbolKind(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    TYPE_ALIAS = auto()


@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    location: SourceLocation
    declared_type: TypeAnnotation | None = None
    mutable: bool = True
    param_count: int | None = None
    param_names: list[str] | None = None
    builtin: bool = False
    imported: bool = False
