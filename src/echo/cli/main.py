from __future__ import annotations

import argparse
import sys
from pathlib import Path

from echo import __version__
from echo.errors import (
    ArgumentError,
    EchoError,
    EchoExit,
    EchoIndexError,
    EchoNameError,
    EchoTypeError,
    LexError,
    ModuleLoadError,
    MutationError,
    ParseError,
    SemanticError,
    SourceLocation,
    format_diagnostic,
)
from echo.formatter import format_source
from echo.linter import LintFinding, lint_source
from echo.frontend.ast.nodes import ImportDeclaration, Program
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.frontend.tokens import TokenType
from echo.modules.loader import ModuleLoader
from echo.modules.records import Module
from echo.runtime.context import Environment
from echo.runtime.functions import EchoFunction
from echo.runtime.host import Host
from echo.runtime.interpreter import Interpreter
from echo.semantics.analyzer import SemanticAnalyzer
from echo.semantics.modules import ModuleSymbols
from echo.semantics.scope import Scope

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
    except EchoExit as exc:
        return exc.code
    except EchoError as exc:
        _print_error(exc, source, plain)
        return 1


def check_file(source_path: str, plain: bool = False) -> int:
    file_path = Path(source_path).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        _print_plain_error("Error", f"source file not found: {file_path}", plain)
        return 1
    source = file_path.read_text(encoding="utf-8")
    try:
        tokens = Lexer().tokenize(source, filename=str(file_path))
        program = Parser(tokens).parse()
        if _has_imports(program):
            ModuleLoader().check(file_path)
        else:
            SemanticAnalyzer().analyze(program)
        return 0
    except EchoError as exc:
        _print_error(exc, _error_source(exc, source), plain)
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
    except EchoExit as exc:
        return exc.code
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
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw[:1] == ["check"]:
        return _main_check(raw[1:])
    if raw[:1] == ["test"]:
        return _main_test(raw[1:])
    if raw[:1] == ["fmt"]:
        return _main_fmt(raw[1:])
    if raw[:1] == ["lint"]:
        return _main_lint(raw[1:])
    parser = argparse.ArgumentParser(description="Run an Echo source file")
    parser.add_argument("source", nargs="?", help="Path to .echo source file")
    parser.add_argument("--plain", action="store_true", help="Disable Rich styling and use plain text output")
    parser.add_argument("--version", action="store_true", help="Print the Echo version and exit")
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
    host = Host(args=list(program_args))
    if not args.source:
        return run_repl(plain=args.plain, host=host)
    return run_file(args.source, plain=args.plain, host=host)


def run_repl(*, plain: bool = True, host: Host | None = None) -> int:
    host = host or Host()
    interpreter = Interpreter(host=host)
    env = Environment()
    session_scope = SemanticAnalyzer.module_scope(SourceLocation(1, 1, "<repl>"))
    loader = ModuleLoader()
    print(f"Echo {__version__}")
    buffer: list[str] = []
    while True:
        prompt = "echo> " if not buffer else "... "
        try:
            line = input(prompt)
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            buffer.clear()
            continue
        if not buffer and not line.strip():
            continue
        buffer.append(line)
        source = "\n".join(buffer)
        if _repl_source_incomplete(source):
            continue
        buffer.clear()
        try:
            session_scope = _run_repl_snippet(source, interpreter, env, session_scope, loader)
        except EchoExit as exc:
            return exc.code
        except EchoError as exc:
            _print_error(exc, source, plain)
        except KeyboardInterrupt:
            print()
        except Exception:
            _print_plain_error("Execution Error", "unexpected error", plain)


def _run_repl_snippet(
    source: str,
    interpreter: Interpreter,
    env: Environment,
    session_scope: Scope,
    loader: ModuleLoader,
) -> Scope:
    tokens = Lexer().tokenize(source, filename="<repl>")
    program = Parser(tokens).parse()
    snippet_scope = session_scope.copy()
    dependencies = _repl_import_dependencies(program, loader)
    SemanticAnalyzer().analyze(program, dependencies=dependencies, scope=snippet_scope)
    _repl_bind_imports(program, loader, env, interpreter.host)
    interpreter.execute(program, env)
    return snippet_scope


def _repl_import_dependencies(program: Program, loader: ModuleLoader) -> dict[str, ModuleSymbols]:
    if not _has_imports(program):
        return {}
    importer = Path.cwd() / "<repl>"
    dependencies: dict[str, ModuleSymbols] = {}
    for statement in program.statements:
        if not isinstance(statement, ImportDeclaration) or statement.module in dependencies:
            continue
        path = loader.resolver.resolve(importer, statement.module)
        module = loader.check(path)
        dependencies[statement.module] = SemanticAnalyzer().collect_symbols(module.ast)
    return dependencies


def _repl_bind_imports(program: Program, loader: ModuleLoader, env: Environment, host: Host) -> None:
    if not _has_imports(program):
        return
    importer = Path.cwd() / "<repl>"
    loaded: dict[str, Module] = {}
    for statement in program.statements:
        if not isinstance(statement, ImportDeclaration):
            continue
        if statement.module not in loaded:
            path = loader.resolver.resolve(importer, statement.module)
            loaded[statement.module] = loader.load(path, host=host)
        value = _repl_export_value(loaded[statement.module], statement.name)
        if isinstance(value, EchoFunction):
            env.define_function(statement.name, value)
        env.define(statement.name, value, mutable=False)


def _repl_export_value(module: Module, name: str) -> object:
    module_env = module.env
    if module_env is None:
        raise ModuleLoadError(
            f"module '{module.path.name}' is not fully initialized",
            code="E3005",
        )
    if name in module_env.values:
        return module_env.values[name]
    function = module_env.functions.get(name)
    if function is not None:
        return function
    raise ModuleLoadError(
        f"module '{module.path.name}' has no export '{name}'",
        code="E3005",
    )


def _repl_source_incomplete(source: str) -> bool:
    try:
        tokens = Lexer().tokenize(source, filename="<repl>")
    except LexError as exc:
        return "closing \"\"\"" in exc.message or "closing '''" in exc.message
    except EchoError:
        return False
    depth = 0
    for token in tokens:
        if token.type is TokenType.COMMENT:
            continue
        if token.type is TokenType.LEFT_BRACE:
            depth += 1
        elif token.type is TokenType.RIGHT_BRACE:
            depth -= 1
            if depth < 0:
                return False
    return depth > 0


def _main_check(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="echo check", description="Analyze Echo source files without running them")
    parser.add_argument("paths", nargs="*", help="Files or directories of .echo sources")
    parser.add_argument("--plain", action="store_true", help="Disable Rich styling and use plain text output")
    args = parser.parse_args(argv)
    if not args.paths:
        parser.print_help()
        return 2
    status = 0
    for raw_path in args.paths:
        collected = _collect_echo_files(raw_path, args.plain)
        if isinstance(collected, int):
            return collected
        for file_path in collected:
            code = check_file(str(file_path), plain=args.plain)
            if code != 0:
                status = code
    return status


def format_file(source_path: str, *, check: bool = False, plain: bool = False) -> int:
    file_path = Path(source_path).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        _print_plain_error("Error", f"source file not found: {file_path}", plain)
        return 1
    source = file_path.read_text(encoding="utf-8")
    try:
        formatted = format_source(source, filename=str(file_path))
    except EchoError as exc:
        _print_error(exc, _error_source(exc, source), plain)
        return 1
    if formatted == source:
        return 0
    if check:
        print(file_path)
        return 1
    file_path.write_text(formatted, encoding="utf-8")
    return 0


def _collect_echo_files(source_path: str, plain: bool) -> list[Path] | int:
    path = Path(source_path).expanduser().resolve()
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.rglob("*.echo") if item.is_file())
    _print_plain_error("Error", f"source file not found: {path}", plain)
    return 1


def _main_fmt(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="echo fmt", description="Format Echo source files")
    parser.add_argument("paths", nargs="*", help="Files or directories of .echo sources")
    parser.add_argument("--check", action="store_true", help="Exit 1 if any file would change")
    parser.add_argument("--plain", action="store_true", help="Disable Rich styling and use plain text output")
    args = parser.parse_args(argv)
    if not args.paths:
        parser.print_help()
        return 2
    status = 0
    for raw_path in args.paths:
        collected = _collect_echo_files(raw_path, args.plain)
        if isinstance(collected, int):
            return collected
        for file_path in collected:
            code = format_file(str(file_path), check=args.check, plain=args.plain)
            if code != 0:
                status = code
    return status


def lint_file(source_path: str, *, plain: bool = False) -> tuple[int, list[LintFinding]]:
    file_path = Path(source_path).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        _print_plain_error("Error", f"source file not found: {file_path}", plain)
        return 1, []
    source = file_path.read_text(encoding="utf-8")
    try:
        findings = lint_source(source, filename=str(file_path))
    except EchoError as exc:
        _print_error(exc, _error_source(exc, source), plain)
        return 1, []
    return (1 if findings else 0), findings


def _main_lint(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="echo lint", description="Lint Echo source files for style and convention")
    parser.add_argument("paths", nargs="*", help="Files or directories of .echo sources")
    parser.add_argument("--plain", action="store_true", help="Disable Rich styling and use plain text output")
    args = parser.parse_args(argv)
    if not args.paths:
        parser.print_help()
        return 2
    status = 0
    for raw_path in args.paths:
        collected = _collect_echo_files(raw_path, args.plain)
        if isinstance(collected, int):
            return collected
        for file_path in collected:
            code, findings = lint_file(str(file_path), plain=args.plain)
            for finding in findings:
                print(finding.format())
            if code != 0:
                status = code
    return status


def _main_test(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="echo test", description="Run Echo tests")
    parser.add_argument("paths", nargs="*", help="Test files or directories of *_test.echo files")
    parser.add_argument("--plain", action="store_true", help="Disable Rich styling and use plain text output")
    args = parser.parse_args(argv)
    if not args.paths:
        parser.print_help()
        return 2
    from echo.cli.test_runner import print_summary, run_tests

    code, results = run_tests(args.paths, plain=args.plain)
    if not results and code != 0:
        return code
    print_summary(results)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
