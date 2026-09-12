from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from echo.errors import SourceLocation
from echo.frontend.ast.nodes import ExportDeclaration, FunctionDeclaration, Program


def is_test_entry(name: str, parameter_count: int) -> bool:
    return name.startswith("test") and parameter_count == 0


def test_unit_matches(name: str, pattern: str) -> bool:
    """Match a `testXxx` unit name with a glob (`*` / exact), case-sensitive."""
    return fnmatch.fnmatchcase(name, pattern)


@dataclass(frozen=True)
class ExpectFailure:
    code: str
    message: str
    detail: str | None = None
    location: SourceLocation | None = None


@dataclass
class TestSession:
    """Records expect* failures for one `echo test` interpreter."""

    _failures: list[ExpectFailure] = field(default_factory=list)

    def record(
        self,
        code: str,
        message: str,
        *,
        detail: str | None = None,
        location: SourceLocation | None = None,
    ) -> None:
        self._failures.append(ExpectFailure(code=code, message=message, detail=detail, location=location))

    def take(self) -> list[ExpectFailure]:
        failures = self._failures
        self._failures = []
        return failures


def discover_test_functions(program: Program) -> list[FunctionDeclaration]:
    found: list[FunctionDeclaration] = []
    for statement in program.statements:
        declaration: FunctionDeclaration | None = None
        if isinstance(statement, FunctionDeclaration):
            declaration = statement
        elif isinstance(statement, ExportDeclaration) and isinstance(statement.declaration, FunctionDeclaration):
            declaration = statement.declaration
        if declaration is not None and is_test_entry(declaration.name, len(declaration.parameters)):
            found.append(declaration)
    return found
