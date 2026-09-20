from echo.formatter import format_source
from echo.frontend.ast.nodes import ClassDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_new_field_block():
    declaration = parse_source(
        """
class Point {
    new {
        x: int;
        y: int;
    }
}
"""
    ).statements[0]
    assert isinstance(declaration, ClassDeclaration)
    assert [field.name for field in declaration.fields] == ["x", "y"]


def test_methods_may_surround_new_block():
    result = run_echo(
        """
class Point {
    fn describe(this) {
        say(this.x);
    }

    new {
        x: int;
        y: int;
    }

    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }
}

p: Point = Point { x: 3, y: 4 };
say(p.length());
p.describe();
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["25", "3"]


def test_empty_class_may_omit_new():
    result = run_echo(
        """
class Marker { }
m: Marker = Marker {};
say(type(m));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Marker"


def test_empty_new_block_is_allowed():
    result = run_echo(
        """
class Marker {
    new { }
}
m: Marker = Marker {};
say(type(m));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Marker"


def test_bare_fields_are_a_parse_error():
    result = run_echo(
        """
class Point {
    x: int;
    y: int;
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "new {" in result.output


def test_duplicate_new_block_is_a_parse_error():
    result = run_echo(
        """
class Point {
    new { x: int; }
    new { y: int; }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "new" in result.output.lower()


def test_formatter_emits_new_block():
    formatted = format_source(
        """
class Point {
new {
x: int;
y: int;
}
fn length(this) -> int {
return this.x;
}
}
"""
    )
    assert "new {" in formatted
    assert "x: int;" in formatted
    assert "fn length(this) -> int" in formatted


def test_construction_unchanged():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int;
    }
}
p: Point = Point { x: 3, y: 4 };
say(p.x);
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "4"]
