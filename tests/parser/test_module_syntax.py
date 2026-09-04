from echo.errors import ParseError
from echo.frontend.ast.nodes import (
    CallExpression,
    ExportDeclaration,
    ExpressionStatement,
    FunctionDeclaration,
    ImportDeclaration,
    Program,
    UseStatement,
    VariableDeclaration,
)
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser


def parse_source(source: str) -> Program:
    return Parser(Lexer().tokenize(source)).parse()


def test_import_add_from_math():
    program = parse_source('import add from "math";')
    statement = program.statements[0]
    assert isinstance(statement, ImportDeclaration)
    assert statement.name == "add"
    assert statement.module == "math"


def test_import_foo_from_utils():
    program = parse_source('import foo from "utils";')
    statement = program.statements[0]
    assert isinstance(statement, ImportDeclaration)
    assert statement.name == "foo"
    assert statement.module == "utils"


def test_export_add():
    program = parse_source("export add;")
    statement = program.statements[0]
    assert isinstance(statement, ExportDeclaration)
    assert statement.name == "add"
    assert statement.declaration is None


def test_multiple_imports():
    program = parse_source(
        """
        import add from "math";
        import join from "utils";
        """
    )
    assert [statement.name for statement in program.statements] == ["add", "join"]
    assert [statement.module for statement in program.statements] == ["math", "utils"]
    assert all(isinstance(statement, ImportDeclaration) for statement in program.statements)


def test_multiple_exports():
    program = parse_source(
        """
        export add;
        export pi;
        """
    )
    assert [statement.name for statement in program.statements] == ["add", "pi"]
    assert all(isinstance(statement, ExportDeclaration) for statement in program.statements)


def test_import_plus_normal_statements():
    program = parse_source(
        """
        import add from "math";
        say(add(2, 3));
        """
    )
    assert len(program.statements) == 2
    imported = program.statements[0]
    call = program.statements[1]
    assert isinstance(imported, ImportDeclaration)
    assert imported.name == "add"
    assert imported.module == "math"
    assert isinstance(call, ExpressionStatement)
    assert isinstance(call.expression, CallExpression)


def test_export_plus_function():
    program = parse_source(
        """
        export fn add(a: int, b: int) -> int {
            return a + b;
        }
        """
    )
    statement = program.statements[0]
    assert isinstance(statement, ExportDeclaration)
    assert statement.name == "add"
    assert isinstance(statement.declaration, FunctionDeclaration)
    assert statement.declaration.name == "add"
    assert [parameter.name for parameter in statement.declaration.parameters] == ["a", "b"]


def test_export_variable_declaration():
    program = parse_source("export x: int = 10;")
    statement = program.statements[0]
    assert isinstance(statement, ExportDeclaration)
    assert statement.name == "x"
    assert isinstance(statement.declaration, VariableDeclaration)
    assert statement.declaration.name == "x"


def test_parser_does_not_resolve_module_names():
    program = parse_source('import add from "math";')
    statement = program.statements[0]
    assert isinstance(statement, ImportDeclaration)
    assert statement.module == "math"
    assert statement.module != "math.echo"


def test_malformed_import_missing_name():
    try:
        parse_source('import from "math";')
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_malformed_import_missing_from():
    try:
        parse_source('import add "math";')
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_malformed_import_missing_string():
    try:
        parse_source("import add from math;")
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_malformed_export():
    try:
        parse_source("export;")
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_wildcard_import_is_rejected():
    try:
        parse_source('import * from "math";')
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_import_alias_is_rejected():
    try:
        parse_source('import add as plus from "math";')
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_multi_name_import_is_rejected():
    try:
        parse_source('import add, multiply from "math";')
        assert False, "expected ParseError"
    except ParseError:
        pass


def test_use_grammar_is_unchanged():
    program = parse_source(
        """
        fn bump() {
            use mut x;
            x = x + 1;
        }
        """
    )
    function = program.statements[0]
    assert isinstance(function, FunctionDeclaration)
    assert isinstance(function.body[0], UseStatement)
    assert function.body[0].names == ["x"]
    assert function.body[0].mutable is True
