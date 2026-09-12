from contextlib import redirect_stdout
from io import StringIO

from echo.cli.main import main
from echo.errors import ParseError
from echo.formatter import format_source
from echo.frontend.ast.nodes import ExportDeclaration, VariableDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.frontend.tokens import TokenType
from echo.linter import lint_source
from helpers import ExecutionResult, assert_no_python_leak, run_echo
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def _run_main(argv: list[str]) -> tuple[int, str]:
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main(argv)
    return code, stdout.getvalue()


def test_const_declare_read_and_say():
    result = run_echo(
        """
const name: str = "Echo";
const count: int = 2;
say(name, count);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Echo 2"


def test_const_reassignment_is_analyze_error():
    result = run_echo(
        """
const n: int = 1;
n = 2;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3201" in result.output
    assert "const" in result.output.lower()


def test_const_compound_assignment_is_analyze_error():
    result = run_echo(
        """
const n: int = 1;
n += 1;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3201" in result.output


def test_frozen_list_push_aborts():
    result = run_echo(
        """
const xs: list = [1, 2];
xs.push(3);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3202" in result.output
    assert "const" in result.output.lower()


def test_frozen_list_index_assign_aborts():
    result = run_echo(
        """
const xs: list = [1, 2];
xs[0] = 9;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3202" in result.output


def test_frozen_hash_field_set_aborts():
    result = run_echo(
        """
const user: hash = { name: "Echo" };
user["name"] = "Ada";
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3202" in result.output


def test_map_and_unique_on_const_list_return_new_lists():
    result = run_echo(
        """
fn double(x: int) -> int {
    return x * 2;
}
const xs: list = [1, 1, 2];
say(xs.map(double));
say(xs.unique());
say(xs);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[2, 2, 4]", "[1, 2]", "[1, 1, 2]"]


def test_passing_frozen_list_into_mutating_fn_aborts():
    result = run_echo(
        """
const xs: list = [1, 2];
fn bump(ys: list) {
    ys.push(3);
}
bump(xs);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3203" in result.output
    assert "frozen" in result.output.lower()


def test_alias_of_frozen_list_still_aborts():
    result = run_echo(
        """
const xs: list = [1];
ys: list = xs;
ys.push(2);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3203" in result.output


def test_clone_of_frozen_list_is_mutable():
    result = run_echo(
        """
const xs: list = [1];
ys: list = xs.clone();
ys.push(2);
say(xs);
say(ys);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1]", "[1, 2]"]


def test_nested_list_via_other_name_is_not_frozen():
    result = run_echo(
        """
inner: list = [1];
const xs: list = [inner];
inner.push(2);
say(xs);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[[1, 2]]"


def test_reverse_on_const_string_is_allowed():
    result = run_echo(
        """
const s: str = "ab";
say(s.reverse());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "ba"


def test_export_const_can_be_imported_and_read(tmp_path):
    write_modules(
        tmp_path,
        {
            "config.echo": """
                export const n: int = 7;
            """,
            "app.echo": """
                import n from "config";
                say(n);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "7")


def test_export_const_cannot_be_reassigned(tmp_path):
    write_modules(
        tmp_path,
        {
            "config.echo": """
                export const n: int = 7;
            """,
            "app.echo": """
                import n from "config";
                n = 8;
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "n")
    assert "E3201" in result.output


def test_export_const_list_cannot_be_pushed(tmp_path):
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export const values: list = [1, 2];
            """,
            "app.echo": """
                import values from "data";
                values.push(3);
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "values")
    assert "E3202" in result.output


def test_ordinary_imported_list_stays_mutable(tmp_path):
    write_modules(
        tmp_path,
        {
            "data.echo": """
                export values: list = [1, 2, 3];
            """,
            "app.echo": """
                import values from "data";
                values.push(4);
                say(values);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "[1, 2, 3, 4]")


def test_use_mut_on_const_is_analyze_error():
    result = run_echo(
        """
const n: int = 1;
fn bump() {
    use mut n;
    n = n + 1;
}
bump();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3204" in result.output


def test_watch_on_const_is_legal():
    result = run_echo(
        """
const n: int = 1;
watch n;
say(n);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_const_must_be_initialized():
    try:
        parse_source("const n: int;")
        assert False, "expected ParseError"
    except ParseError as exc:
        assert "initialized" in str(exc).lower()


def test_const_requires_type_annotation():
    try:
        parse_source("const n = 1;")
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_param_const_is_not_parsed():
    try:
        parse_source("fn f(const x: int) { say(x); }")
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_const_keyword_token():
    tokens = Lexer().tokenize("const n: int = 1;")
    types = [token.type for token in tokens if token.type != TokenType.EOF]
    assert types[0] == TokenType.CONST


def test_parse_const_and_export_const():
    program = parse_source("const n: int = 1;")
    statement = program.statements[0]
    assert isinstance(statement, VariableDeclaration)
    assert statement.const
    assert statement.name == "n"

    exported = parse_source("export const n: int = 1;").statements[0]
    assert isinstance(exported, ExportDeclaration)
    assert isinstance(exported.declaration, VariableDeclaration)
    assert exported.declaration.const


def test_formatter_prints_const():
    formatted = format_source("const x:int=1;")
    assert formatted == "const x: int = 1;\n"
    assert format_source(formatted) == formatted

    exported = format_source("export const n:int=7;")
    assert exported == "export const n: int = 7;\n"


def test_lint_unused_const():
    findings = lint_source("const x: int = 1;\nsay(2);\n")
    assert any(finding.rule == "unused-local" and "x" in finding.message for finding in findings)


def test_fmt_check_lint_on_const_file(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text("const x:int=1;\nsay(x);\n", encoding="utf-8")

    code, output = _run_main(["fmt", str(app), "--plain"])
    assert code == 0
    assert output == ""
    assert app.read_text(encoding="utf-8") == "const x: int = 1;\nsay(x);\n"

    code, output = _run_main(["check", str(app), "--plain"])
    assert code == 0
    assert output == ""

    code, output = _run_main(["lint", str(app), "--plain"])
    assert code == 0
    assert output == ""

    dirty = tmp_path / "bad.echo"
    dirty.write_text("const n: int = 1;\nn = 2;\n", encoding="utf-8")
    code, output = _run_main(["check", str(dirty), "--plain"])
    result = ExecutionResult(code, output)
    assert code == 1
    assert_no_python_leak(result)
    assert "E3201" in output
