from __future__ import annotations

from echo.errors import SemanticError
from echo.frontend.ast.nodes import TypeAnnotation
from echo.semantics.symbols import Symbol, SymbolKind


class Scope:
    def __init__(self, parent: Scope | None = None, *, is_function: bool = False, is_loop: bool = False):
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}
        self.is_function = is_function
        self.is_loop = is_loop or (parent.is_loop if parent else False)
        self.in_function = is_function or (parent.in_function if parent else False)
        self.type_aliases: dict[str, TypeAnnotation] = {}
        if parent:
            self.type_aliases = dict(parent.type_aliases)

    def define(self, symbol: Symbol) -> None:
        existing = self.symbols.get(symbol.name)
        if existing is not None and not existing.builtin:
            kind = "function" if existing.kind == SymbolKind.FUNCTION else "name"
            hint = (
                "A function with this name is already defined in this scope."
                if existing.kind == SymbolKind.FUNCTION
                else "Use assignment without a type to update an existing variable."
            )
            raise SemanticError(
                f"{kind.capitalize()} '{symbol.name}' is already declared",
                symbol.location,
                help_text=hint,
                code="E1001",
            )
        self.symbols[symbol.name] = symbol

    def resolve(self, name: str) -> Symbol | None:
        current: Scope | None = self
        while current:
            symbol = current.symbols.get(name)
            if symbol is not None:
                return symbol
            current = current.parent
        return None

    def contains_local(self, name: str) -> bool:
        return name in self.symbols

    def enclosing_function(self) -> Scope | None:
        current: Scope | None = self
        while current:
            if current.is_function:
                return current
            current = current.parent
        return None
