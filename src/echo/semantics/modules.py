from __future__ import annotations

from dataclasses import dataclass, field

from echo.semantics.symbols import Symbol


@dataclass
class ModuleSymbols:
    private: dict[str, Symbol] = field(default_factory=dict)
    exports: dict[str, Symbol] = field(default_factory=dict)
    imports: dict[str, Symbol] = field(default_factory=dict)
