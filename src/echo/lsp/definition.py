from __future__ import annotations

from pathlib import Path

from echo.errors import SourceLocation
from echo.frontend.ast.nodes import (
    ClassDeclaration,
    DestructureDeclaration,
    ExportDeclaration,
    ForeachStatement,
    ForStatement,
    FunctionDeclaration,
    IfStatement,
    ImportDeclaration,
    InterfaceDeclaration,
    Parameter,
    Program,
    Statement,
    SwitchStatement,
    VariableDeclaration,
    WhileStatement,
    iter_name_patterns,
)
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.lsp.hover import identifier_at
from echo.lsp.protocol import echo_to_lsp_position, lsp_to_echo_position, path_to_uri, uri_to_path
from echo.modules.resolver import ModuleResolveError, ModuleResolver
from echo.runtime.builtins import builtin_names
from echo.semantics.analyzer import SemanticAnalyzer


def definition_at(uri: str, text: str, line: int, character: int) -> list[dict]:
    """Return LSP Location[] for textDocument/definition (local + imported)."""
    echo_line, echo_col = lsp_to_echo_position(line, character)
    path = uri_to_path(uri)
    filename = path or uri or "<lsp>"
    name = identifier_at(text, echo_line, echo_col, filename=filename)
    if name is None or name in builtin_names():
        return []

    try:
        tokens = Lexer().tokenize(text, filename=filename)
        program = Parser(tokens).parse()
    except Exception:  # noqa: BLE001 — definition is best-effort
        return []

    # Imported name (on the import line or at a use site) → export in the dependency.
    for statement in program.statements:
        if isinstance(statement, ImportDeclaration) and statement.name == name:
            target = _import_export_location(path, statement.module, name)
            if target is not None:
                return _locations_from_source_location(target, name)

    local = _resolve_local(program, name, echo_line, echo_col)
    if local is None:
        return []
    return _locations_from_source_location(local, name, fallback_uri=uri)


def _import_export_location(importer: str | None, specifier: str, name: str) -> SourceLocation | None:
    if importer is None:
        return None
    importer_path = Path(importer)
    try:
        dep = ModuleResolver().resolve(importer_path, specifier)
    except ModuleResolveError:
        return None
    if not dep.is_file():
        return None
    try:
        source = dep.read_text(encoding="utf-8")
        tokens = Lexer().tokenize(source, filename=str(dep))
        program = Parser(tokens).parse()
        symbols = SemanticAnalyzer().collect_symbols(program)
    except Exception:  # noqa: BLE001
        return None
    if name in symbols.exports:
        return symbols.exports[name].location
    if name in symbols.classes:
        return symbols.classes[name].location
    if name in symbols.interfaces:
        return symbols.interfaces[name].location
    return None


def _locations_from_source_location(
    location: SourceLocation | None,
    name: str,
    *,
    fallback_uri: str | None = None,
) -> list[dict]:
    if location is None:
        return []
    line = location.line
    column = location.column
    if location.filename:
        column = _name_column_on_line(location.filename, line, column, name)
        uri = path_to_uri(location.filename)
    elif fallback_uri:
        uri = fallback_uri
    else:
        return []
    start = echo_to_lsp_position(line, column)
    end = {
        "line": start["line"],
        "character": start["character"] + max(len(name), 1),
    }
    return [{"uri": uri, "range": {"start": start, "end": end}}]


def _name_column_on_line(filename: str, line: int, column: int, name: str) -> int:
    """Prefer the identifier column when the node location points at a keyword."""
    try:
        text = Path(filename).read_text(encoding="utf-8")
    except OSError:
        return column
    lines = text.splitlines()
    if not (1 <= line <= len(lines)):
        return column
    row = lines[line - 1]
    # Search from the reported column (1-based) for the name token.
    start_index = max(column - 1, 0)
    found = row.find(name, start_index)
    if found < 0:
        found = row.find(name)
    if found < 0:
        return column
    return found + 1


def _resolve_local(program: Program, name: str, line: int, column: int) -> SourceLocation | None:
    eof_line = _eof_line(program)
    return _resolve_in_statements(program.statements, name, line, column, {}, 1, eof_line + 1)


def _eof_line(program: Program) -> int:
    if not program.statements:
        return program.location.line
    last = program.statements[-1]
    return _statement_end_line(last, last.location.line)


def _statement_end_line(statement: Statement, fallback: int) -> int:
    bodies = _nested_statement_lists(statement)
    fn = _as_function(statement)
    if fn is not None:
        if isinstance(fn.body, list):
            bodies = [fn.body]
        else:
            return getattr(fn.body, "location", statement.location).line
    if not bodies:
        return statement.location.line
    ends = [fallback]
    for body in bodies:
        if not body:
            continue
        ends.append(max(_statement_end_line(item, item.location.line) for item in body))
    return max(ends)


def _resolve_in_statements(
    statements: list[Statement],
    name: str,
    line: int,
    column: int,
    parent_bindings: dict[str, SourceLocation],
    span_start: int,
    span_end: int,
) -> SourceLocation | None:
    bindings = dict(parent_bindings)

    for statement in statements:
        fn = _as_function(statement)
        if fn is not None:
            bindings[fn.name] = fn.location
        if isinstance(statement, ClassDeclaration):
            bindings[statement.name] = statement.location
        if isinstance(statement, InterfaceDeclaration):
            bindings[statement.name] = statement.location
        if isinstance(statement, ExportDeclaration):
            if isinstance(statement.declaration, ClassDeclaration):
                bindings[statement.declaration.name] = statement.declaration.location
            if isinstance(statement.declaration, InterfaceDeclaration):
                bindings[statement.declaration.name] = statement.declaration.location

    for index, statement in enumerate(statements):
        next_start = statements[index + 1].location.line if index + 1 < len(statements) else span_end
        stmt_end = max(next_start, _statement_end_line(statement, statement.location.line) + 1)

        if isinstance(statement, VariableDeclaration):
            bindings[statement.name] = statement.location
        elif isinstance(statement, DestructureDeclaration):
            for pattern in iter_name_patterns(statement.pattern):
                bindings[pattern.name] = pattern.location
        elif isinstance(statement, ExportDeclaration) and isinstance(statement.declaration, VariableDeclaration):
            bindings[statement.declaration.name] = statement.declaration.location

        fn = _as_function(statement)
        if fn is not None and statement.location.line <= line < stmt_end:
            child = _resolve_in_function(fn, name, line, column, bindings)
            if child is not None:
                return child

        if isinstance(statement, ForeachStatement) and statement.location.line <= line < stmt_end:
            loop_bindings = dict(bindings)
            loop_bindings[statement.var] = statement.location
            child = _resolve_in_statements(
                statement.body, name, line, column, loop_bindings, statement.location.line, stmt_end
            )
            if child is not None:
                return child

        if isinstance(statement, ForStatement) and statement.location.line <= line < stmt_end:
            loop_bindings = dict(bindings)
            loop_bindings[statement.var] = statement.location
            child = _resolve_in_statements(
                statement.body, name, line, column, loop_bindings, statement.location.line, stmt_end
            )
            if child is not None:
                return child

        for nested in _nested_statement_lists(statement):
            if statement.location.line <= line < stmt_end:
                child = _resolve_in_statements(
                    nested, name, line, column, bindings, statement.location.line, stmt_end
                )
                if child is not None:
                    return child

    if span_start <= line < span_end and name in bindings:
        return bindings[name]
    return None


def _resolve_in_function(
    function: FunctionDeclaration,
    name: str,
    line: int,
    column: int,
    parent_bindings: dict[str, SourceLocation],
) -> SourceLocation | None:
    bindings = dict(parent_bindings)
    bindings[function.name] = function.location
    for parameter in function.parameters:
        bindings[parameter.name] = _parameter_location(parameter, function)
    body = function.body
    if isinstance(body, list):
        end = _statement_end_line(function, function.location.line) + 1
        found = _resolve_in_statements(body, name, line, column, bindings, function.location.line, end)
        if found is not None:
            return found
        if function.location.line <= line < end and name in bindings:
            return bindings[name]
        return None
    if function.location.line <= line and name in bindings:
        return bindings[name]
    return None


def _parameter_location(parameter: Parameter, function: FunctionDeclaration) -> SourceLocation:
    location = getattr(parameter, "location", None)
    if isinstance(location, SourceLocation):
        return location
    return function.location


def _as_function(statement: Statement) -> FunctionDeclaration | None:
    if isinstance(statement, FunctionDeclaration):
        return statement
    if isinstance(statement, ExportDeclaration) and isinstance(statement.declaration, FunctionDeclaration):
        return statement.declaration
    return None


def _nested_statement_lists(statement: Statement) -> list[list[Statement]]:
    nested: list[list[Statement]] = []
    if isinstance(statement, IfStatement):
        nested.append(statement.then_branch)
        if statement.else_branch:
            nested.append(statement.else_branch)
    elif isinstance(statement, WhileStatement):
        nested.append(statement.body)
    elif isinstance(statement, SwitchStatement):
        for arm in statement.arms:
            nested.append(arm.body)
    return nested
