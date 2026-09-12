from pathlib import Path

from echo.linter import lint_source

FIXTURES = Path(__file__).parent / "fixtures"


def _rules(source: str) -> list[str]:
    return [finding.rule for finding in lint_source(source, filename="app.echo")]


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _fixture_rules(name: str) -> list[str]:
    return [finding.rule for finding in lint_source(_fixture(name), filename=name)]


def test_unused_local():
    findings = lint_source("x: int = 1;\nsay(2);\n", filename="app.echo")
    assert len(findings) == 1
    assert findings[0].rule == "unused-local"
    assert "x" in findings[0].message
    assert findings[0].line == 1


def test_unused_function():
    findings = lint_source("fn helper() {\n    say(1);\n}\n", filename="app.echo")
    assert [finding.rule for finding in findings] == ["unused-function"]
    assert "helper" in findings[0].message


def test_unused_import():
    findings = lint_source('import add from "math";\nsay(1);\n', filename="app.echo")
    assert [finding.rule for finding in findings] == ["unused-import"]
    assert "add" in findings[0].message


def test_comparison_to_bool():
    source = """
flag: bool = true;
if flag == true {
    say("yes");
}
"""
    assert "comparison-to-bool" in _rules(source)


def test_redundant_by_one():
    source = """
for i: int in 1..3 by 1 {
    say(i);
}
"""
    assert "redundant-by-one" in _rules(source)


def test_for_without_by_is_clean():
    source = """
for i: int in 1..3 {
    say(i);
}
"""
    assert _rules(source) == []


def test_empty_if_body():
    source = """
if true {
}
"""
    assert _rules(source) == ["empty-block"]


def test_empty_function_body():
    source = """
fn noop() {
}
noop();
"""
    assert _rules(source) == ["empty-block"]


def test_shadow_builtin():
    source = """
length: int = 1;
eprint(length);
"""
    assert _rules(source) == ["shadow-builtin"]


def test_exported_function_is_not_unused():
    source = """
export fn add(a: int, b: int) -> int {
    return a + b;
}
"""
    assert _rules(source) == []


def test_zero_arg_test_function_is_not_unused():
    source = """
fn testAdd() {
    expect(true, "ok");
}

fn helper() {
    say(1);
}
"""
    findings = lint_source(source, filename="app_test.echo")
    assert [finding.rule for finding in findings] == ["unused-function"]
    assert "helper" in findings[0].message


def test_parameterized_test_function_is_unused():
    source = """
fn testAdd(n: int) {
    say(n);
}
"""
    findings = lint_source(source, filename="app_test.echo")
    assert {finding.rule for finding in findings} == {"unused-function", "test-naming"}
    assert all("testAdd" in finding.message for finding in findings)


def test_used_names_are_clean():
    source = """
import add from "math";
fn greet(user: str) {
    say(user);
}
x: int = add(1, 2);
greet("Echo");
say(x);
"""
    assert _rules(source) == []


def test_unused_parameter_is_unused_local():
    source = """
fn greet(user: str) {
    say(1);
}
greet("Echo");
"""
    assert _rules(source) == ["unused-local"]
    findings = lint_source(source, filename="app.echo")
    assert "user" in findings[0].message


def test_test_naming_fixture():
    findings = lint_source(_fixture("test-naming.echo"), filename="test-naming.echo")
    named = [finding for finding in findings if finding.rule == "test-naming"]
    messages = [finding.message for finding in named]
    assert [finding.rule for finding in named] == ["test-naming", "test-naming", "test-naming"]
    assert any("testAdd" in message for message in messages)
    assert any("testing" in message for message in messages)
    assert any("TestAdd" in message for message in messages)
    assert all(finding.format().startswith("test-naming.echo:") for finding in named)
    assert all(": test-naming: " in finding.format() for finding in named)


def test_test_naming_ok_fixture_is_clean():
    assert _fixture_rules("test-naming-ok.echo") == []


def test_test_naming_skips_nested_functions():
    source = """
fn outer() {
    fn testNested() {
        expect(true, "nested");
    }
    testNested();
}
outer();
"""
    assert "test-naming" not in _rules(source)


def test_self_assign_fixture():
    findings = lint_source(_fixture("self-assign.echo"), filename="self-assign.echo")
    assert [finding.rule for finding in findings] == ["self-assign", "self-assign", "self-assign"]
    assert [finding.message for finding in findings] == [
        "self-assignment of 'x'",
        "self-assignment of 'y'",
        "self-assignment of 'z'",
    ]


def test_self_assign_ok_fixture_is_clean():
    assert _fixture_rules("self-assign-ok.echo") == []


def test_self_assign_ignores_bool_zero():
    source = """
flag: bool = false;
flag = flag + false;
say(flag);
"""
    assert "self-assign" not in _rules(source)


def test_unreachable_after_fail_fixture():
    findings = lint_source(
        _fixture("unreachable-after-fail.echo"),
        filename="unreachable-after-fail.echo",
    )
    assert [finding.rule for finding in findings] == ["unreachable-after-fail", "unreachable-after-fail"]
    assert findings[0].message == "unreachable code after return"
    assert findings[1].message == "unreachable code after fail"


def test_unreachable_after_fail_ok_fixture_is_clean():
    assert _fixture_rules("unreachable-after-fail-ok.echo") == []


def test_lambda_unused_param_and_empty_body():
    source = """
fn run(cb: fn(int) -> int) {
    say(cb(1));
}
run(fn(x: int) -> int { return 1; });
run(fn() {});
"""
    rules = _rules(source)
    assert "unused-local" in rules
    assert "empty-block" in rules


def test_unreachable_after_fail_same_block_only():
    source = """
fail("stop");
say("dead");
say("also dead");
"""
    findings = lint_source(source, filename="app.echo")
    assert [finding.rule for finding in findings] == ["unreachable-after-fail", "unreachable-after-fail"]
    assert findings[0].format() == "app.echo:3:1: unreachable-after-fail: unreachable code after fail"
