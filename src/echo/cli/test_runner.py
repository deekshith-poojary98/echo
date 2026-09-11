from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from echo.errors import EchoError, EchoExit, format_diagnostic
from echo.frontend.ast.nodes import ImportDeclaration, Program
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.modules.loader import ModuleLoader
from echo.runtime.context import Environment
from echo.runtime.functions import EchoFunction
from echo.runtime.interpreter import Interpreter
from echo.runtime.testing import ExpectFailure, TestSession, discover_test_functions
from echo.semantics.analyzer import SemanticAnalyzer


@dataclass
class TestUnitResult:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)


def collect_test_files(source_path: str) -> list[Path] | str:
    path = Path(source_path).expanduser().resolve()
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.rglob("*_test.echo") if item.is_file())
    return f"source file not found: {path}"


def run_tests(paths: list[str], *, plain: bool) -> tuple[int, list[TestUnitResult]]:
    _ = plain
    files: list[Path] = []
    seen: set[Path] = set()
    for raw_path in paths:
        collected = collect_test_files(raw_path)
        if isinstance(collected, str):
            print(f"Error: {collected}")
            return 1, []
        for item in collected:
            if item in seen:
                continue
            seen.add(item)
            files.append(item)

    results: list[TestUnitResult] = []
    for file_path in files:
        for result in run_test_file(file_path):
            print_unit(result)
            results.append(result)
    return (0 if all(result.passed for result in results) else 1), results


def run_test_file(path: Path) -> list[TestUnitResult]:
    display = _display_path(path)
    session = TestSession()
    interpreter = Interpreter(test_session=session)
    source = ""
    try:
        source = path.read_text(encoding="utf-8")
        tokens = Lexer().tokenize(source, filename=str(path))
        program = Parser(tokens).parse()
        if _has_imports(program):
            module = ModuleLoader().load(path, host=interpreter.host, interpreter=interpreter)
            program = module.ast
            env = module.env if module.env is not None else Environment()
        else:
            SemanticAnalyzer().analyze(program)
            env = Environment()
            interpreter.execute(program, env)
    except EchoExit as exc:
        return [_result_from_finish(display, session.take(), abort=None, exit_code=exc.code, source=source)]
    except EchoError as exc:
        return [_result_from_finish(display, session.take(), abort=exc, exit_code=None, source=source)]

    test_fns = discover_test_functions(program)
    setup_failures = session.take()
    if not test_fns:
        return [_result_from_finish(display, setup_failures, abort=None, exit_code=None, source=source)]

    results: list[TestUnitResult] = []
    if setup_failures:
        results.append(_result_from_finish(display, setup_failures, abort=None, exit_code=None, source=source))

    for declaration in test_fns:
        name = f"{display}::{declaration.name}"
        function = env.resolve_function(declaration.name)
        if not isinstance(function, EchoFunction):
            results.append(
                TestUnitResult(
                    name=name,
                    passed=False,
                    details=[f"Error: test function '{declaration.name}' is not defined"],
                )
            )
            continue
        try:
            interpreter.call_function_with_values(function, [], declaration.location)
        except EchoExit as exc:
            results.append(
                _result_from_finish(name, session.take(), abort=None, exit_code=exc.code, source=source)
            )
            continue
        except EchoError as exc:
            results.append(
                _result_from_finish(name, session.take(), abort=exc, exit_code=None, source=source)
            )
            continue
        results.append(
            _result_from_finish(name, session.take(), abort=None, exit_code=None, source=source)
        )
    return results


def print_unit(result: TestUnitResult) -> None:
    prefix = "ok   " if result.passed else "FAIL "
    print(f"{prefix}{result.name}")
    for line in result.details:
        print(f"     {line}")


def print_summary(results: list[TestUnitResult]) -> None:
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    print(f"{passed} passed, {failed} failed")


def _result_from_finish(
    name: str,
    failures: list[ExpectFailure],
    *,
    abort: EchoError | None,
    exit_code: int | None,
    source: str,
) -> TestUnitResult:
    details: list[str] = []
    for failure in failures:
        details.extend(_expect_lines(failure))
    if abort is not None:
        details.extend(_error_lines(abort, source))
    elif exit_code is not None and exit_code != 0:
        details.append(f"exit code {exit_code}")
    passed = abort is None and (exit_code is None or exit_code == 0) and not failures
    return TestUnitResult(name=name, passed=passed, details=details)


def _expect_lines(failure: ExpectFailure) -> list[str]:
    lines = [f"Error[{failure.code}]: {failure.message}"]
    if failure.detail:
        lines.append(failure.detail)
    if failure.location is not None:
        lines.append(f"--> {failure.location}")
    return lines


def _error_lines(error: EchoError, source: str) -> list[str]:
    diagnostic_source = _error_source(error, source)
    help_text = error.help_text
    error.help_text = None
    message = format_diagnostic(error, diagnostic_source)
    error.help_text = help_text
    lines = message.splitlines()
    if help_text:
        lines.append(f"Hint: {help_text}")
    return lines


def _error_source(error: EchoError, fallback: str) -> str:
    if error.location is None or error.location.filename is None:
        return fallback
    origin = Path(error.location.filename)
    if not origin.is_file():
        return fallback
    return origin.read_text(encoding="utf-8")


def _has_imports(program: Program) -> bool:
    return any(isinstance(statement, ImportDeclaration) for statement in program.statements)


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()
