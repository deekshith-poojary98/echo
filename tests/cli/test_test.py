from contextlib import redirect_stdout
from io import StringIO

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
