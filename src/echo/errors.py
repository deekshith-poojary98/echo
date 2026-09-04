from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    line: int
    column: int
    filename: str | None = None

    def __str__(self) -> str:
        origin = self.filename or "<input>"
        return f"{origin}:{self.line}:{self.column}"


class EchoError(Exception):
    def __init__(
        self,
        message: str,
        location: SourceLocation | None = None,
        help_text: str | None = None,
        code: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.location = location
        self.help_text = help_text
        self.code = code

    def __str__(self) -> str:
        if self.location is None:
            return self.message
        return f"{self.message} ({self.location})"


class LexError(EchoError):
    pass


class ParseError(EchoError):
    pass


class SemanticError(EchoError):
    pass


class EchoRuntimeError(EchoError):
    pass


class EchoTypeError(EchoRuntimeError):
    pass


class EchoNameError(EchoRuntimeError):
    pass


class ArgumentError(EchoRuntimeError):
    pass


class EchoIndexError(EchoRuntimeError):
    pass


class MutationError(EchoRuntimeError):
    pass


class ModuleResolveError(EchoError):
    pass


class ModuleGraphError(EchoError):
    pass


class ModuleLoadError(EchoError):
    pass


def format_diagnostic(error: EchoError, source: str | None = None) -> str:
    header = f"Error[{error.code}]: {error.message}" if error.code else f"Error: {error.message}"
    lines = [header]

    if error.location is not None:
        loc = error.location
        lines.append(f"  --> {loc}")
        if source:
            source_lines = source.splitlines()
            if 1 <= loc.line <= len(source_lines):
                text = source_lines[loc.line - 1]
                lines.append(f"   |")
                lines.append(f"{loc.line:>3} | {text}")
                caret = " " * (loc.column - 1) + "^"
                lines.append(f"   | {caret}")

    if error.help_text:
        lines.append("")
        lines.append(f"help: {error.help_text}")

    return "\n".join(lines)
