from __future__ import annotations

from echo.errors import EchoError, SourceLocation
from echo.frontend.ast.nodes import ImportDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.lsp.protocol import echo_to_lsp_position, uri_to_path
from echo.modules.loader import ModuleLoader
from echo.runtime.host import Host
from echo.semantics.analyzer import SemanticAnalyzer


def collect_diagnostics(uri: str, text: str, host: Host | None = None) -> list[dict]:
    """Run check-style analysis and return LSP Diagnostic objects."""
    host = host or Host()
    path = uri_to_path(uri)
    filename = path or uri or "<lsp>"
    try:
        tokens = Lexer().tokenize(text, filename=filename)
        program = Parser(tokens).parse()
        has_imports = any(isinstance(stmt, ImportDeclaration) for stmt in program.statements)
        if has_imports and path is not None:
            from pathlib import Path

            file_path = Path(path)
            if file_path.is_file():
                # Prefer module graph when the file exists on disk (may lag dirty buffers).
                ModuleLoader().check(file_path, host=host)
            else:
                SemanticAnalyzer().analyze(
                    program,
                    scope=SemanticAnalyzer.prelude_scope(program.location, host),
                )
        else:
            SemanticAnalyzer().analyze(
                program,
                scope=SemanticAnalyzer.prelude_scope(program.location, host),
            )
        return []
    except EchoError as exc:
        return [_echo_error_to_diagnostic(exc, text)]


def _echo_error_to_diagnostic(error: EchoError, source: str) -> dict:
    location = error.location
    start = echo_to_lsp_position(
        location.line if location else 1,
        location.column if location else 1,
    )
    end = _estimate_end(start, source)
    message = error.message
    if error.code:
        message = f"[{error.code}] {message}"
    if error.help_text:
        message = f"{message}\n{error.help_text}"
    diagnostic: dict = {
        "range": {"start": start, "end": end},
        "severity": 1,  # Error
        "source": "echo",
        "message": message,
    }
    if error.code:
        diagnostic["code"] = error.code
    return diagnostic


def _estimate_end(start: dict[str, int], source: str) -> dict[str, int]:
    line_index = start["line"]
    lines = source.splitlines()
    if 0 <= line_index < len(lines):
        line_text = lines[line_index]
        col = start["character"]
        end_col = col + 1
        if col < len(line_text) and (line_text[col].isalnum() or line_text[col] == "_"):
            cursor = col
            while cursor < len(line_text) and (line_text[cursor].isalnum() or line_text[cursor] == "_"):
                cursor += 1
            end_col = max(cursor, col + 1)
        return {"line": line_index, "character": end_col}
    return {"line": start["line"], "character": start["character"] + 1}
