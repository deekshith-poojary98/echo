from __future__ import annotations

import json
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
from echo.runtime.testing import ExpectFailure, TestSession, discover_test_functions, test_unit_matches
from echo.semantics.analyzer import SemanticAnalyzer


@dataclass
class TestUnitResult:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)
    skipped: bool = False
    message: str | None = None
    location: str | None = None


def collect_test_files(source_path: str) -> list[Path] | str:
    path = Path(source_path).expanduser().resolve()
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.rglob("*_test.echo") if item.is_file())
    return f"source file not found: {path}"


def run_tests(
    paths: list[str],
    *,
    plain: bool,
    run: str | None = None,
    json_output: bool = False,
) -> tuple[int, list[TestUnitResult]]:
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
        for result in run_test_file(file_path, run=run):
            if not json_output and not result.skipped:
                print_unit(result)
            results.append(result)
    ran = [result for result in results if not result.skipped]
    return (0 if all(result.passed for result in ran) else 1), results


def run_test_file(path: Path, *, run: str | None = None) -> list[TestUnitResult]:
    display = _display_path(path)
    session = TestSession()
    interpreter = Interpreter(test_session=session)
    source = ""
    program = None
    try:
        source = path.read_text(encoding="utf-8")
        tokens = Lexer().tokenize(source, filename=str(path))
        program = Parser(tokens).parse()
        if run is not None:
            discovered = discover_test_functions(program)
            if not any(test_unit_matches(declaration.name, run) for declaration in discovered):
                if discovered:
                    return [_skipped_unit(f"{display}::{declaration.name}") for declaration in discovered]
                return [_skipped_unit(display)]
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
    all_test_fns = test_fns
    if run is not None:
        test_fns = [declaration for declaration in test_fns if test_unit_matches(declaration.name, run)]
        if not test_fns:
            if all_test_fns:
                return [_skipped_unit(f"{display}::{declaration.name}") for declaration in all_test_fns]
            return [_skipped_unit(display)]
    setup_failures = session.take()
    if not test_fns:
        return [_result_from_finish(display, setup_failures, abort=None, exit_code=None, source=source)]

    results: list[TestUnitResult] = []
    if setup_failures:
        results.append(_result_from_finish(display, setup_failures, abort=None, exit_code=None, source=source))

    skipped_names = {
        declaration.name
        for declaration in all_test_fns
        if run is not None and not test_unit_matches(declaration.name, run)
    }
    for declaration in all_test_fns:
        name = f"{display}::{declaration.name}"
        if declaration.name in skipped_names:
            results.append(_skipped_unit(name))
            continue
        function = env.resolve_function(declaration.name)
        if not isinstance(function, EchoFunction):
            results.append(
                TestUnitResult(
                    name=name,
                    passed=False,
                    details=[f"Error: test function '{declaration.name}' is not defined"],
                    message=f"Error: test function '{declaration.name}' is not defined",
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
    ran = [result for result in results if not result.skipped]
    passed = sum(1 for result in ran if result.passed)
    failed = len(ran) - passed
    print(f"{passed} passed, {failed} failed")


def format_json_report(results: list[TestUnitResult]) -> dict:
    units: list[dict] = []
    passed = failed = skipped = 0
    for result in results:
        entry: dict = {"name": result.name}
        if result.skipped:
            entry["skipped"] = True
            skipped += 1
        else:
            entry["passed"] = result.passed
            if result.passed:
                passed += 1
            else:
                failed += 1
                if result.message is not None:
                    entry["message"] = result.message
                if result.location is not None:
                    entry["location"] = result.location
        units.append(entry)
    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "units": units,
    }


def print_json_report(results: list[TestUnitResult]) -> None:
    print(json.dumps(format_json_report(results), ensure_ascii=False))


def _skipped_unit(name: str) -> TestUnitResult:
    return TestUnitResult(name=name, passed=True, skipped=True)


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
    message, location = _failure_fields(failures, abort=abort, exit_code=exit_code)
    return TestUnitResult(
        name=name,
        passed=passed,
        details=details,
        message=message,
        location=location,
    )


def _failure_fields(
    failures: list[ExpectFailure],
    *,
    abort: EchoError | None,
    exit_code: int | None,
) -> tuple[str | None, str | None]:
    if abort is not None:
        message = f"Error[{abort.code}]: {abort.message}" if abort.code else abort.message
        location = str(abort.location) if abort.location is not None else None
        return message, location
    if failures:
        first = failures[0]
        message = f"Error[{first.code}]: {first.message}"
        location = str(first.location) if first.location is not None else None
        return message, location
    if exit_code is not None and exit_code != 0:
        return f"exit code {exit_code}", None
    return None, None


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
