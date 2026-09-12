from contextlib import redirect_stdout
from io import StringIO
import json

from echo.cli.main import main
from helpers import ExecutionResult, assert_no_python_leak


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_expect_failure_continues_in_one_unit(tmp_path):
    app = tmp_path / "cont_test.echo"
    app.write_text(
        """
fn testBoth() {
    expect(false, "first");
    expect(false, "second");
    say("still-ran");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 1
    assert "still-ran" in output
    assert "first" in output
    assert "second" in output
    assert "E2826" in output
    assert "FAIL" in output
    assert "::testBoth" in output
    assert "0 passed, 1 failed" in output


def test_expect_eq_and_neq(tmp_path):
    app = tmp_path / "eq_test.echo"
    app.write_text(
        """
fn testEqPass() {
    expectEq(1 + 1, 2, "add");
}

fn testEqFail() {
    expectEq(4 - 1, 4, "sub");
}

fn testNeqPass() {
    expectNeq(1, 2, "differ");
}

fn testNeqFail() {
    expectNeq(3, 3, "same");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 1
    assert "::testEqPass" in output
    assert "::testEqFail" in output
    assert "::testNeqPass" in output
    assert "::testNeqFail" in output
    assert "expected 4, got 3" in output
    assert "E2827" in output
    assert "E2828" in output
    assert "2 passed, 2 failed" in output


def test_test_star_functions_are_separate_units(tmp_path):
    app = tmp_path / "units_test.echo"
    app.write_text(
        """
say("setup");

fn helper(n: int) -> int {
    return n + 1;
}

fn testAdd() {
    expectEq(helper(1), 2, "add");
}

fn testMul() {
    expectEq(2 * 3, 6, "mul");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "--plain"])
    assert code == 0
    assert "setup" in output
    assert output.count("ok   ") == 2
    assert "::testAdd" in output
    assert "::testMul" in output
    assert "2 passed, 0 failed" in output
    assert "::helper" not in output


def test_directory_discovers_star_test_echo_only(tmp_path):
    nested = tmp_path / "suite" / "inner"
    nested.mkdir(parents=True)
    discovered = tmp_path / "suite" / "foo_test.echo"
    nested_test = nested / "bar_test.echo"
    helper = tmp_path / "suite" / "helper.echo"
    other = tmp_path / "suite" / "test.echo"
    discovered.write_text("fn testOk() {\n    expect(true, \"ok\");\n}\n", encoding="utf-8")
    nested_test.write_text("fn testOk() {\n    expect(true, \"ok\");\n}\n", encoding="utf-8")
    helper.write_text('fail("helper should not run");\n', encoding="utf-8")
    other.write_text('fail("test.echo should not run from a directory");\n', encoding="utf-8")
    code, output = _run_main(["test", str(tmp_path / "suite"), "--plain"])
    assert code == 0
    assert "foo_test.echo" in output
    assert "bar_test.echo" in output
    assert "helper.echo" not in output
    assert "helper should not run" not in output
    assert "test.echo should not run" not in output
    assert "2 passed, 0 failed" in output


def test_explicit_non_test_filename_still_runs(tmp_path):
    helper = tmp_path / "helper.echo"
    helper.write_text('expect(true, "ok");\n', encoding="utf-8")
    code, output = _run_main(["test", str(helper), "--plain"])
    assert code == 0
    assert "helper.echo" in output
    assert "1 passed, 0 failed" in output


def test_summary_exit_codes(tmp_path):
    passing = tmp_path / "ok_test.echo"
    failing = tmp_path / "bad_test.echo"
    passing.write_text("fn testOk() {\n    expect(true, \"ok\");\n}\n", encoding="utf-8")
    failing.write_text('expect(false, "nope");\n', encoding="utf-8")
    code, output = _run_main(["test", str(passing), "--plain"])
    assert code == 0
    assert "1 passed, 0 failed" in output
    code, output = _run_main(["test", str(failing), "--plain"])
    assert code == 1
    assert "0 passed, 1 failed" in output


def test_assert_and_fail_abort_unit_later_units_run(tmp_path):
    app = tmp_path / "abort_test.echo"
    app.write_text(
        """
fn testAssert() {
    assert(false, "asserted");
    expect(false, "should-not-run");
}

fn testFail() {
    fail("failed");
    say("after-fail");
}

fn testLater() {
    expect(true, "ok");
    say("later");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 1
    assert "asserted" in output
    assert "E2819" in output
    assert "should-not-run" not in output
    assert "failed" in output
    assert "E2825" in output
    assert "after-fail" not in output
    assert "later" in output
    assert "::testLater" in output
    assert "1 passed, 2 failed" in output


def test_echo_test_no_path_prints_help_and_fails():
    code, output = _run_main(["test"])
    assert code == 2
    assert "usage" in output.lower()
    assert "echo test" in output
    assert "passed" not in output


def test_parse_error_fails_that_unit_later_files_run(tmp_path):
    bad = tmp_path / "bad_test.echo"
    good = tmp_path / "good_test.echo"
    bad.write_text("say(1)\n", encoding="utf-8")
    good.write_text("fn testOk() {\n    expect(true, \"ok\");\n}\n", encoding="utf-8")
    code, output = _run_main(["test", str(bad), str(good), "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 1
    assert "FAIL" in output
    assert "Error" in output
    assert "::testOk" in output
    assert "1 passed, 1 failed" in output


def test_run_filters_function_units_not_file_names(tmp_path):
    app = tmp_path / "units_test.echo"
    app.write_text(
        """
say("setup");

fn testAdd() {
    expectEq(1 + 1, 2, "add");
}

fn testMul() {
    expectEq(2 * 3, 6, "mul");
}

fn testAdder() {
    fail("should-not-run");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "-run", "testAdd", "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 0
    assert "setup" in output
    assert "::testAdd" in output
    assert "::testMul" not in output
    assert "::testAdder" not in output
    assert "should-not-run" not in output
    assert "1 passed, 0 failed" in output

    code, output = _run_main(["test", str(app), "--run", "*Add*", "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 1
    assert "::testAdd" in output
    assert "::testAdder" in output
    assert "::testMul" not in output
    assert "1 passed, 1 failed" in output


def test_run_skips_file_with_no_matching_units(tmp_path):
    app = tmp_path / "units_test.echo"
    app.write_text(
        """
say("setup");

fn testAdd() {
    fail("add");
}

fn testMul() {
    fail("mul");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "-run", "testNone", "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 0
    assert "setup" not in output
    assert "FAIL" not in output
    assert "::testAdd" not in output
    assert "0 passed, 0 failed" in output


def test_run_skips_file_unit_without_test_functions(tmp_path):
    app = tmp_path / "bare_test.echo"
    app.write_text('fail("should-not-run");\n', encoding="utf-8")
    code, output = _run_main(["test", str(app), "-run", "testAdd", "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 0
    assert "should-not-run" not in output
    assert "0 passed, 0 failed" in output


def test_run_with_directory_and_plain(tmp_path):
    suite = tmp_path / "suite"
    suite.mkdir()
    add_file = suite / "add_test.echo"
    mul_file = suite / "mul_test.echo"
    add_file.write_text(
        """
fn testAdd() {
    expect(true, "add");
}

fn testOther() {
    fail("other");
}
""",
        encoding="utf-8",
    )
    mul_file.write_text(
        """
fn testMul() {
    fail("mul");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(suite), "-run", "*Add*", "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 0
    assert "add_test.echo::testAdd" in output
    assert "testOther" not in output
    assert "mul_test.echo" not in output
    assert "1 passed, 0 failed" in output
    assert "FAIL" not in output


def test_json_report_pass_fail_and_no_human_summary(tmp_path):
    app = tmp_path / "units_test.echo"
    app.write_text(
        """
fn testOk() {
    expect(true, "ok");
}

fn testFail() {
    expect(false, "nope");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "--json"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 1
    assert "ok   " not in output
    assert "FAIL " not in output
    assert " passed, " not in output
    report = json.loads(output)
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["skipped"] == 0
    units = {unit["name"].rsplit("::", 1)[-1]: unit for unit in report["units"]}
    assert units["testOk"]["passed"] is True
    assert "message" not in units["testOk"]
    assert units["testFail"]["passed"] is False
    assert units["testFail"]["message"] == "Error[E2826]: nope"
    assert "location" in units["testFail"]
    assert "units_test.echo" in units["testFail"]["location"]
    assert ":5:" in units["testFail"]["location"] or units["testFail"]["location"].count(":") >= 2


def test_json_composes_with_run_and_plain(tmp_path):
    app = tmp_path / "units_test.echo"
    app.write_text(
        """
fn testAdd() {
    expectEq(1 + 1, 2, "add");
}

fn testMul() {
    expectEq(2 * 3, 6, "mul");
}

fn testAdder() {
    fail("should-not-run");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "-run", "*Add*", "--json", "--plain"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 1
    assert "ok   " not in output
    assert "FAIL " not in output
    assert " passed, " not in output
    report = json.loads(output)
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["skipped"] == 1
    by_name = {unit["name"].rsplit("::", 1)[-1]: unit for unit in report["units"]}
    assert by_name["testAdd"]["passed"] is True
    assert by_name["testAdder"]["passed"] is False
    assert "should-not-run" in by_name["testAdder"]["message"]
    assert "location" in by_name["testAdder"]
    assert by_name["testMul"]["skipped"] is True
    assert "passed" not in by_name["testMul"]


def test_json_skipped_file_with_no_matching_units(tmp_path):
    app = tmp_path / "units_test.echo"
    app.write_text(
        """
fn testAdd() {
    fail("add");
}

fn testMul() {
    fail("mul");
}
""",
        encoding="utf-8",
    )
    code, output = _run_main(["test", str(app), "--run", "testNone", "--json"])
    result = ExecutionResult(code, output)
    assert_no_python_leak(result)
    assert code == 0
    report = json.loads(output)
    assert report["passed"] == 0
    assert report["failed"] == 0
    assert report["skipped"] == 2
    names = {unit["name"].rsplit("::", 1)[-1] for unit in report["units"]}
    assert names == {"testAdd", "testMul"}
    assert all(unit.get("skipped") is True for unit in report["units"])


def test_json_exit_codes_unchanged(tmp_path):
    passing = tmp_path / "ok_test.echo"
    failing = tmp_path / "bad_test.echo"
    passing.write_text("fn testOk() {\n    expect(true, \"ok\");\n}\n", encoding="utf-8")
    failing.write_text('expect(false, "nope");\n', encoding="utf-8")
    code, output = _run_main(["test", str(passing), "--json"])
    assert code == 0
    report = json.loads(output)
    assert report["passed"] == 1
    assert report["failed"] == 0
    code, output = _run_main(["test", str(failing), "--json"])
    assert code == 1
    report = json.loads(output)
    assert report["passed"] == 0
    assert report["failed"] == 1
    assert "nope" in report["units"][0]["message"]
    code, output = _run_main(["test", "--json"])
    assert code == 2
    assert "usage" in output.lower()


