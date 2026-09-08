from __future__ import annotations

import argparse
import sys
from pathlib import Path

from echo import __version__
from echo.errors import (
    ArgumentError,
    EchoError,
    EchoIndexError,
    EchoNameError,
    EchoTypeError,
    LexError,
    MutationError,
    ParseError,
    SemanticError,
    format_diagnostic,
)
from echo.frontend.ast.nodes import ImportDeclaration, Program
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.modules.loader import ModuleLoader
from echo.runtime.host import Host
from echo.runtime.interpreter import Interpreter
from echo.semantics.analyzer import SemanticAnalyzer

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    Console = None
    Panel = None


def run_source(source: str, filename: str = "<input>", *, plain: bool = True, host: Host | None = None) -> int:
    try:
        tokens = Lexer().tokenize(source, filename=filename)
        program = Parser(tokens).parse()
        SemanticAnalyzer().analyze(program)
        Interpreter(host=host).execute(program)
        return 0
    except EchoError as exc:
        _print_error(exc, source, plain)
        return 1


def run_file(source_path: str, plain: bool = False, host: Host | None = None) -> int:
    file_path = Path(source_path).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        _print_plain_error("Error", f"source file not found: {file_path}", plain)
        return 1
    source = file_path.read_text(encoding="utf-8")
    try:
        tokens = Lexer().tokenize(source, filename=str(file_path))
        program = Parser(tokens).parse()
        if _has_imports(program):
            ModuleLoader().load(file_path, host=host)
        else:
            SemanticAnalyzer().analyze(program)
            Interpreter(host=host).execute(program)
        return 0
    except EchoError as exc:
        _print_error(exc, _error_source(exc, source), plain)
        return 1


def _has_imports(program: Program) -> bool:
    return any(isinstance(statement, ImportDeclaration) for statement in program.statements)


def _error_source(error: EchoError, fallback: str) -> str:
    if error.location is None or error.location.filename is None:
        return fallback
    origin = Path(error.location.filename)
    if not origin.is_file():
        return fallback
    return origin.read_text(encoding="utf-8")


def _category(error: EchoError) -> str:
    if isinstance(error, LexError):
        return "Syntax Error"
    if isinstance(error, ParseError):
        return "Syntax Error"
    if isinstance(error, SemanticError):
        return "Semantic Error"
    if isinstance(error, EchoNameError):
        return "Name Error"
    if isinstance(error, EchoTypeError):
        return "Type Error"
    if isinstance(error, ArgumentError):
        return "Argument Error"
    if isinstance(error, EchoIndexError):
        return "Index Error"
    if isinstance(error, MutationError):
        return "Mutation Error"
    return "Execution Error"


def _print_error(error: EchoError, source: str, plain: bool) -> None:
    help_text = error.help_text
    error.help_text = None
    message = format_diagnostic(error, source)
    error.help_text = help_text
    title = _category(error)
    _print_plain_error(title, message, plain)
    if help_text:
        _print_plain_error("Hint", help_text, plain)


def _print_plain_error(title: str, message: str, plain: bool) -> None:
    if not plain and Console is not None and Panel is not None:
        Console().print(Panel(message, title=title, border_style="red", expand=False))
        return
    print(f"{title}: {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an Echo source file")
    parser.add_argument("source", nargs="?", help="Path to .echo source file")
    parser.add_argument("--plain", action="store_true", help="Disable Rich styling and use plain text output")
    parser.add_argument("--version", action="store_true", help="Print the Echo version and exit")
    raw = list(sys.argv[1:] if argv is None else argv)
    if "--" in raw:
        split_at = raw.index("--")
        interpreter_argv, program_args = raw[:split_at], raw[split_at + 1 :]
        args, unknown = parser.parse_known_args(interpreter_argv)
        if unknown:
            parser.error(f"unrecognized arguments: {' '.join(unknown)}")
    else:
        args, program_args = parser.parse_known_args(raw)

    if args.version:
        print(f"Echo {__version__}")
        return 0
    if not args.source:
        parser.print_help()
        return 2
    host = Host(args=list(program_args))
    return run_file(args.source, plain=args.plain, host=host)


if __name__ == "__main__":
    raise SystemExit(main())
