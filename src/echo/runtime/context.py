from __future__ import annotations

from echo.errors import EchoNameError, MutationError, SourceLocation
from echo.frontend.ast.nodes import TypeAnnotation
from echo.runtime.values import validate_type


class Environment:
    def __init__(self, parent: Environment | None = None, *, is_function: bool = False):
        self.parent = parent
        self.values: dict[str, object] = {}
        self.types: dict[str, TypeAnnotation | str | None] = {}
        self.functions: dict[str, object] = {}
        self.is_function = is_function
        self.mutable_imports: set[str] = set()
        self.readonly_imports: set[str] = set()
        self.watched: set[str] = set()
        self.function_name: str | None = None

    def enclosing_function(self) -> Environment | None:
        current: Environment | None = self
        while current:
            if current.is_function:
                return current
            current = current.parent
        return None

    def is_within(self, ancestor: Environment) -> bool:
        current: Environment | None = self
        while current:
            if current is ancestor:
                return True
            current = current.parent
        return False

    def define(self, name: str, value: object, var_type: TypeAnnotation | str | None = None) -> None:
        self.values[name] = value
        if var_type is not None:
            self.types[name] = var_type

    def is_defined(self, name: str) -> bool:
        current: Environment | None = self
        while current:
            if name in current.values:
                return True
            current = current.parent
        return False

    def get(self, name: str, location: SourceLocation | None = None) -> object:
        current: Environment | None = self
        while current:
            if name in current.values:
                return current.values[name]
            current = current.parent
        raise EchoNameError(f"Variable '{name}' is not defined", location, code="E2002")

    def get_type(self, name: str) -> TypeAnnotation | str | None:
        current: Environment | None = self
        while current:
            if name in current.types:
                return current.types[name]
            current = current.parent
        return None

    def require_mutable(self, name: str, location: SourceLocation | None = None) -> None:
        target = self._find_binding(name)
        if target is None:
            raise EchoNameError(f"Variable '{name}' is not defined", location, code="E2002")
        function = self.enclosing_function()
        if function is not None and not target.is_within(function):
            if name not in function.mutable_imports:
                raise MutationError(
                    f"Cannot modify outer variable '{name}' without 'use mut'",
                    location,
                    help_text=f"Use 'use mut {name};' inside the function before mutating that imported variable.",
                    code="E2003",
                )

    def assign(self, name: str, value: object, location: SourceLocation | None = None) -> None:
        target = self._find_binding(name)
        if target is None:
            raise EchoNameError(f"Variable '{name}' is not declared", location, code="E2011")

        function = self.enclosing_function()
        if function is not None and not target.is_within(function):
            if name not in function.mutable_imports:
                raise MutationError(
                    f"Cannot modify outer variable '{name}' without 'use mut'",
                    location,
                    help_text=f"Use 'use mut {name};' inside the function before mutating that imported variable.",
                    code="E2003",
                )
        expected = target.types.get(name, self.get_type(name))
        validate_type(name, value, expected, location)
        target.values[name] = value

    def _find_binding(self, name: str) -> Environment | None:
        current: Environment | None = self
        while current:
            if name in current.values:
                return current
            current = current.parent
        return None

    def import_variable(self, name: str, mutable: bool, location: SourceLocation | None = None) -> None:
        function = self.enclosing_function()
        if function is None:
            raise MutationError("'use' statements can only be used inside functions", location, code="E2004")
        if name in function.mutable_imports or name in function.readonly_imports:
            raise MutationError(f"Variable '{name}' already imported", location, code="E2005")
        if not self.is_defined(name):
            raise EchoNameError(f"Cannot import undefined variable '{name}'", location, code="E2006")
        if mutable:
            function.mutable_imports.add(name)
        else:
            function.readonly_imports.add(name)

    def watch(self, name: str, location: SourceLocation | None = None) -> None:
        if not self.is_defined(name):
            raise EchoNameError(f"Cannot watch undefined variable '{name}'", location, code="E2007")
        self.watched.add(name)

    def is_watched(self, name: str) -> bool:
        current: Environment | None = self
        while current:
            if name in current.watched:
                return True
            current = current.parent
        return False

    def current_function_name(self) -> str:
        current: Environment | None = self
        while current:
            if current.function_name:
                return current.function_name
            current = current.parent
        return "global"

    def define_function(self, name: str, function: object) -> None:
        self.functions[name] = function

    def resolve_function(self, name: str) -> object | None:
        current: Environment | None = self
        while current:
            if name in current.functions:
                return current.functions[name]
            current = current.parent
        return None
