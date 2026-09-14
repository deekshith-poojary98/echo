from contextlib import redirect_stdout
from io import StringIO

from echo.cli.main import main
from echo.errors import ParseError
from echo.formatter import format_source
from echo.frontend.ast.nodes import (
    DestructureAssignment,
    DestructureDeclaration,
    FunctionDeclaration,
    HashPattern,
    ListPattern,
    NamePattern,
)
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.linter import lint_source
from helpers import ExecutionResult, assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_list_declare_and_say():
    result = run_echo(
        """
pair: list = [1, 2];
[a: int, b: int] = pair;
say(a, b);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1 2"


def test_hash_declare_and_say():
    result = run_echo(
        """
user: hash = { id: 7, name: "Ada" };
{ id: int, name: str } = user;
say(id, name);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "7 Ada"


def test_const_list_destructure():
    result = run_echo(
        """
bounds: list = [1, 4];
const [lo: int, hi: int] = bounds;
say(lo, hi);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1 4"


def test_const_destructure_cannot_reassign():
    result = run_echo(
        """
const [n: int] = [1];
n = 2;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3201" in result.output


def test_assignment_to_existing_names():
    result = run_echo(
        """
a: int = 0;
b: int = 0;
id: int = 0;
name: str = "";
[a, b] = [3, 4];
{ id, name } = { id: 9, name: "Echo" };
say(a, b, id, name);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "3 4 9 Echo"


def test_fn_list_and_hash_params():
    result = run_echo(
        """
fn add([a: int, b: int]) -> int {
    return a + b;
}
fn greet({ name: str }) -> str {
    return name;
}
say(add([2, 3]));
say(greet({ name: "Ada" }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["5", "Ada"]


def test_list_rest_binds_list():
    result = run_echo(
        """
xs: list = [1, 2, 3, 4];
[head: int, rest: int...] = xs;
say(head);
say(rest);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["1", "[2, 3, 4]"]


def test_rest_may_be_empty():
    result = run_echo(
        """
[head: int, rest: int...] = [9];
say(head);
say(rest);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["9", "[]"]


def test_list_length_mismatch_aborts():
    result = run_echo(
        """
pair: list = [1, 2, 3];
[a: int, b: int] = pair;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3205" in result.output


def test_extra_list_elements_without_rest_analyze_error():
    result = run_echo("[a: int, b: int] = [1, 2, 3];")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3205" in result.output


def test_missing_hash_key_aborts():
    result = run_echo(
        """
user: hash = { name: "Ada" };
{ id: int, name: str } = user;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2711" in result.output


def test_extra_hash_keys_ignored():
    result = run_echo(
        """
user: hash = { id: 1, name: "Ada", extra: true };
{ id: int, name: str } = user;
say(id, name);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1 Ada"


def test_nested_list_pattern():
    result = run_echo(
        """
[[a: int], b: int] = [[1], 2];
say(a, b);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1 2"


def test_expected_list_aborts():
    result = run_echo('[a: int] = { id: 1 };')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3206" in result.output


def test_expected_hash_aborts():
    result = run_echo("{ id: int } = [1];")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3207" in result.output


def test_lambda_list_param():
    result = run_echo(
        """
sumPair: fn(list) -> int = fn([a: int, b: int]) -> int { return a + b; };
say(sumPair([4, 5]));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "9"


def test_hash_rest_is_parse_error():
    try:
        parse_source("{ id: int... } = user;")
        assert False, "expected ParseError"
    except ParseError as exc:
        assert "rest" in str(exc).lower()


def test_parse_declare_assign_and_fn_params():
    declared = parse_source("[a: int, b: int] = pair;").statements[0]
    assert isinstance(declared, DestructureDeclaration)
    assert isinstance(declared.pattern, ListPattern)
    assert not declared.const

    assigned = parse_source("[a, b] = pair;").statements[0]
    assert isinstance(assigned, DestructureAssignment)

    hashed = parse_source("{ id: int, name: str } = user;").statements[0]
    assert isinstance(hashed, DestructureDeclaration)
    assert isinstance(hashed.pattern, HashPattern)

    consted = parse_source("const [lo: int, hi: int] = bounds;").statements[0]
    assert isinstance(consted, DestructureDeclaration)
    assert consted.const

    fn = parse_source("fn add([a: int, b: int]) -> int { return a + b; }").statements[0]
    assert isinstance(fn, FunctionDeclaration)
    assert fn.parameters[0].pattern is not None
    assert isinstance(fn.parameters[0].pattern, ListPattern)
    rest_stmt = parse_source("[head: int, rest: int...] = xs;").statements[0]
    assert isinstance(rest_stmt, DestructureDeclaration)
    rest = rest_stmt.pattern.elements[-1]
    assert isinstance(rest, NamePattern)
    assert rest.rest


def test_formatter_prints_destructure():
    assert format_source("[a:int,b:int]=pair;") == "[a: int, b: int] = pair;\n"
    assert format_source("const [lo:int,hi:int]=bounds;") == "const [lo: int, hi: int] = bounds;\n"
    assert format_source("[a,b]=pair;") == "[a, b] = pair;\n"
    assert format_source("{id:int,name:str}=user;") == "{id: int, name: str} = user;\n"
    assert format_source("[head:int,rest:int...]=xs;") == "[head: int, rest: int...] = xs;\n"
    formatted = format_source("fn add([a:int,b:int])->int{return a+b;}")
    assert formatted == "fn add([a: int, b: int]) -> int {\n    return a + b;\n}\n"
    assert format_source(formatted) == formatted


def test_lint_unused_destructure():
    findings = lint_source("[a: int, b: int] = [1, 2];\nsay(1);\n")
    assert any(finding.rule == "unused-local" and "a" in finding.message for finding in findings)
    assert any(finding.rule == "unused-local" and "b" in finding.message for finding in findings)


def test_fmt_check_lint_on_destructure_file(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text("[a:int,b:int]=[1,2];\nsay(a,b);\n", encoding="utf-8")

    code, output = _run_main(["fmt", str(app), "--plain"])
    assert code == 0
    assert output == ""
    assert app.read_text(encoding="utf-8") == "[a: int, b: int] = [1, 2];\nsay(a, b);\n"

    code, output = _run_main(["check", str(app), "--plain"])
    assert code == 0
    assert output == ""

    code, output = _run_main(["lint", str(app), "--plain"])
    assert code == 0
    assert output == ""

    dirty = tmp_path / "bad.echo"
    dirty.write_text("[a: int, b: int] = [1];\n", encoding="utf-8")
    code, output = _run_main(["check", str(dirty), "--plain"])
    result = ExecutionResult(code, output)
    assert code == 1
    assert_no_python_leak(result)
    assert "E3205" in output
