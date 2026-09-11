from __future__ import annotations

import json
import re
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from echo import __version__
from echo.cli.main import main

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_JSON = REPO_ROOT / "echo-syntax-highlighter" / "package.json"

# Captured `echolang … --plain` strings (paths substituted in tests).
CHECK_SEMANTIC = """\
Semantic Error: Error[E2205]: Missing argument for parameter 'b' in function 'add'
  --> {path}:2:5
   |
  2 | say(add(1));
   |     ^
"""

CHECK_PARSE = """\
Syntax Error: Error: Expected ;, got end of input
  --> {path}:2:1
"""

LINT_UNUSED = "{path}:1:1: unused-local: unused local 'x'\n"

TEST_EXPECT_EQ = """\
FAIL {path}::testFail
     Error[E2827]: nope
     expected 2, got 1
     --> {path}:2:5
0 passed, 1 failed
"""

TEST_ABORT = """\
FAIL {path}::testFail
     Error[E2825]: aborted
       --> {path}:3:5
        |
       3 |     fail("aborted");
        |     ^
0 passed, 1 failed
"""


def _package() -> dict:
    return json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))


def _matchers() -> dict[str, dict]:
    return {item["name"]: item for item in _package()["contributes"]["problemMatchers"]}


def _patterns(matcher: dict) -> list[dict]:
    pattern = matcher["pattern"]
    if isinstance(pattern, dict):
        return [pattern]
    return list(pattern)


def apply_matcher(matcher: dict, text: str) -> list[dict[str, str]]:
    """Apply a VS Code-style per-line problem matcher. Returns captured groups."""
    patterns = _patterns(matcher)
    regexes = [re.compile(item["regexp"]) for item in patterns]
    lines = text.splitlines()
    found: list[dict[str, str]] = []
    index = 0
    while index <= len(lines) - len(regexes):
        captured: dict[str, str] = {}
        ok = True
        for offset, (spec, regex) in enumerate(zip(patterns, regexes)):
            match = regex.search(lines[index + offset])
            if match is None:
                ok = False
                break
            for key in ("file", "line", "column", "message", "code"):
                group = spec.get(key)
                if group is None:
                    continue
                value = match.group(group)
                if value is not None:
                    captured[key] = value
        if ok:
            found.append(captured)
            index += len(regexes)
        else:
            index += 1
    return found


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_package_exports_named_matchers_and_tracks_version():
    package = _package()
    root = REPO_ROOT / "echo-syntax-highlighter"
    assert package["version"] == __version__
    assert package["main"] == "./extension.js"
    assert (root / "extension.js").is_file()
    json.loads((root / "snippets" / "echo.json").read_text(encoding="utf-8"))
    tasks = json.loads((root / "templates" / "tasks.json").read_text(encoding="utf-8"))
    names = set(_matchers())
    assert names == {"echo", "echo-lint", "echo-test", "echo-test-detail"}
    commands = {item["command"] for item in package["contributes"]["commands"]}
    assert commands == {
        "echo.checkFile",
        "echo.checkWorkspace",
        "echo.lintWorkspace",
        "echo.formatWorkspace",
        "echo.testWorkspace",
    }
    labels = {item["label"] for item in tasks["tasks"]}
    assert "Echo: Check file" in labels
    assert "Echo: Check workspace" in labels


def test_echo_matcher_on_check_semantic_fixture(tmp_path):
    path = str((tmp_path / "sem.echo").resolve())
    problems = apply_matcher(_matchers()["echo"], CHECK_SEMANTIC.format(path=path))
    assert len(problems) == 1
    problem = problems[0]
    assert problem["file"] == path
    assert problem["line"] == "2"
    assert problem["column"] == "5"
    assert problem["code"] == "E2205"
    assert "Missing argument for parameter 'b'" in problem["message"]


def test_echo_matcher_on_check_parse_fixture_without_code(tmp_path):
    path = str((tmp_path / "bad.echo").resolve())
    problems = apply_matcher(_matchers()["echo"], CHECK_PARSE.format(path=path))
    assert len(problems) == 1
    problem = problems[0]
    assert problem["file"] == path
    assert problem["line"] == "2"
    assert problem["column"] == "1"
    assert "code" not in problem
    assert problem["message"].startswith("Error: Expected ;")


def test_lint_matcher_on_finding_fixture(tmp_path):
    path = str((tmp_path / "lint.echo").resolve())
    problems = apply_matcher(_matchers()["echo-lint"], LINT_UNUSED.format(path=path))
    assert problems == [
        {
            "file": path,
            "line": "1",
            "column": "1",
            "code": "unused-local",
            "message": "unused local 'x'",
        }
    ]


def test_test_matchers_on_expect_eq_and_abort_fixtures(tmp_path):
    path = str((tmp_path / "fail_test.echo").resolve())
    detail = apply_matcher(_matchers()["echo-test-detail"], TEST_EXPECT_EQ.format(path=path))
    assert len(detail) == 1
    assert detail[0]["file"] == path
    assert detail[0]["line"] == "2"
    assert detail[0]["column"] == "5"
    assert detail[0]["code"] == "E2827"
    assert detail[0]["message"] == "Error[E2827]: nope"
    two_line = apply_matcher(_matchers()["echo-test"], TEST_EXPECT_EQ.format(path=path))
    assert two_line == []

    abort = apply_matcher(_matchers()["echo-test"], TEST_ABORT.format(path=path))
    assert len(abort) == 1
    assert abort[0]["file"] == path
    assert abort[0]["line"] == "3"
    assert abort[0]["column"] == "5"
    assert abort[0]["code"] == "E2825"
    assert abort[0]["message"] == "Error[E2825]: aborted"
    abort_detail = apply_matcher(_matchers()["echo-test-detail"], TEST_ABORT.format(path=path))
    assert abort_detail == []


def test_matchers_on_live_plain_cli_output(tmp_path):
    sem = tmp_path / "sem.echo"
    sem.write_text("fn add(a: int, b: int) -> int { return a + b; }\nsay(add(1));\n", encoding="utf-8")
    lint = tmp_path / "lint.echo"
    lint.write_text("x: int = 1;\nsay(2);\n", encoding="utf-8")
    test_file = tmp_path / "fail_test.echo"
    test_file.write_text(
        'fn testFail() {\n    expectEq(1, 2, "nope");\n    fail("aborted");\n}\n',
        encoding="utf-8",
    )

    check_code, check_out = _run_main(["check", str(sem), "--plain"])
    assert check_code == 1
    check_problems = apply_matcher(_matchers()["echo"], check_out)
    assert len(check_problems) == 1
    assert check_problems[0]["file"] == str(sem.resolve())
    assert check_problems[0]["line"] == "2"
    assert check_problems[0]["code"] == "E2205"

    lint_code, lint_out = _run_main(["lint", str(lint), "--plain"])
    assert lint_code == 1
    lint_problems = apply_matcher(_matchers()["echo-lint"], lint_out)
    assert len(lint_problems) == 1
    assert lint_problems[0]["file"] == str(lint.resolve())
    assert lint_problems[0]["code"] == "unused-local"

    test_code, test_out = _run_main(["test", str(test_file), "--plain"])
    assert test_code == 1
    expect_hit = apply_matcher(_matchers()["echo-test-detail"], test_out)
    abort_hit = apply_matcher(_matchers()["echo-test"], test_out)
    assert len(expect_hit) == 1
    assert expect_hit[0]["code"] == "E2827"
    assert expect_hit[0]["file"] == str(test_file.resolve())
    assert len(abort_hit) == 1
    assert abort_hit[0]["code"] == "E2825"
    assert abort_hit[0]["file"] == str(test_file.resolve())
