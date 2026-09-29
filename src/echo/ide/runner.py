"""In-process Echo execution with captured stdout/stderr for the IDE."""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from pathlib import Path

from echo.errors import EchoError, EchoExit, format_diagnostic
from echo.frontend.ast.nodes import ImportDeclaration, Program
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.modules.loader import ModuleLoader
from echo.runtime.host import Host
from echo.runtime.interpreter import Interpreter
from echo.semantics.analyzer import SemanticAnalyzer


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def output(self) -> str:
        return self.stdout + self.stderr


def _has_imports(program: Program) -> bool:
    return any(isinstance(statement, ImportDeclaration) for statement in program.statements)


def run_source(
    source: str,
    *,
    filename: str = "<ide>",
    path: Path | None = None,
    host: Host | None = None,
) -> RunResult:
    """Execute Echo source and return captured stdout/stderr plus exit code."""
    host = host or Host()
    stdout = io.StringIO()
    stderr = io.StringIO()
    interpreter = Interpreter(host=host)
    exit_code = 0

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            tokens = Lexer().tokenize(source, filename=filename)
            program = Parser(tokens).parse()
            if _has_imports(program):
                if path is None or not path.is_file():
                    raise EchoError(
                        "This program uses import. Save the file first, then Run.",
                        code="E3002",
                    )
                # Disk must match the buffer for ModuleLoader; caller should save first.
                ModuleLoader().load(path, host=host, interpreter=interpreter)
            else:
                SemanticAnalyzer().analyze(
                    program,
                    scope=SemanticAnalyzer.prelude_scope(program.location, host),
                )
                interpreter.execute(program)
        except EchoExit as exc:
            exit_code = exc.code
        except EchoError as exc:
            exit_code = 1
            help_text = exc.help_text
            exc.help_text = None
            message = format_diagnostic(exc, source)
            exc.help_text = help_text
            print(message, file=stderr)
            if help_text:
                print(f"Hint: {help_text}", file=stderr)

    return RunResult(exit_code=exit_code, stdout=stdout.getvalue(), stderr=stderr.getvalue())
