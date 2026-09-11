from echo.linter import lint_source


def _rules(source: str) -> list[str]:
    return [finding.rule for finding in lint_source(source, filename="app.echo")]


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
    assert [finding.rule for finding in findings] == ["unused-function"]
    assert "testAdd" in findings[0].message


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
