from echo.formatter import format_source
from echo.frontend.ast.nodes import FunctionDeclaration, LambdaExpression, Parameter
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_const_parameter():
    statement = parse_source("fn f(const xs: list) { say(xs); }").statements[0]
    assert isinstance(statement, FunctionDeclaration)
    param = statement.parameters[0]
    assert isinstance(param, Parameter)
    assert param.const
    assert param.name == "xs"


def test_parser_builds_const_lambda_parameter():
    statement = parse_source("f: fn(list) -> void = fn(const xs: list) { say(xs); };").statements[0]
    assert isinstance(statement.initializer, LambdaExpression)
    assert statement.initializer.parameters[0].const


def test_const_param_rejects_reassignment():
    result = run_echo(
        """
fn bump(const n: int) {
    n = n + 1;
}
bump(1);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3201" in result.output


def test_const_param_rejects_in_place_mutation():
    result = run_echo(
        """
fn grow(const xs: list) {
    xs.push(9);
}
grow([1, 2]);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3202" in result.output


def test_const_param_freezes_shared_list():
    result = run_echo(
        """
fn lock(const xs: list) {
    say(xs);
}
items: list = [1];
lock(items);
items.push(2);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3203" in result.output


def test_const_param_allows_read_and_map():
    result = run_echo(
        """
fn double(x: int) -> int {
    return x * 2;
}
fn show(const xs: list) {
    say(xs.map(double));
    say(xs);
}
show([1, 2]);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[2, 4]", "[1, 2]"]


def test_const_param_with_default():
    result = run_echo(
        """
fn label(const name: str = "Echo") {
    say(name);
}
label();
label("Ada");
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["Echo", "Ada"]


def test_const_variadic_param_is_frozen():
    result = run_echo(
        """
fn take(const xs: int...) {
    xs.push(9);
}
take(1, 2);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3202" in result.output


def test_const_destructure_param():
    result = run_echo(
        """
fn sum(const [a: int, b: int]) -> int {
    return a + b;
}
say(sum([3, 4]));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "7"


def test_const_destructure_param_rejects_reassign():
    result = run_echo(
        """
fn bad(const [a: int, b: int]) {
    a = 9;
}
bad([1, 2]);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3201" in result.output


def test_use_mut_on_const_param_is_e3204():
    result = run_echo(
        """
fn outer(const xs: list) {
    fn inner() {
        use mut xs;
        xs.push(1);
    }
    inner();
}
outer([1]);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3204" in result.output


def test_formatter_prints_const_param():
    assert format_source("fn f(const xs:list){say(xs);}") == "fn f(const xs: list) {\n    say(xs);\n}\n"
    formatted = format_source("fn f(const xs: list = []) { say(xs); }")
    assert "const xs: list" in formatted
    assert format_source(formatted) == formatted
