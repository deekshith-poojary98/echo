from pathlib import Path

from echo.formatter import format_source
from echo.frontend.ast.nodes import ClassDeclaration, FunctionDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo
from modules.harness import assert_success, run_entry, write_modules


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_methods_with_this():
    declaration = parse_source(
        """
class Point {
    new {
    x: int;
    y: int;
    }
    fn length(this) -> int {
        return this.x;
    }
    fn move(this, dx: int, dy: int) -> void {
        this.x = this.x + dx;
    }
}
"""
    ).statements[0]
    assert isinstance(declaration, ClassDeclaration)
    assert len(declaration.methods) == 2
    length = declaration.methods[0]
    assert isinstance(length, FunctionDeclaration)
    assert length.parameters[0].name == "this"
    assert length.parameters[0].type.name == "Point"
    assert declaration.methods[1].parameters[1].name == "dx"


def test_method_call_and_field_mutation():
    result = run_echo(
        """
class Point {
    new {
    x: int;
    y: int;
    }

    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }

    fn move(this, dx: int, dy: int) -> void {
        this.x = this.x + dx;
        this.y = this.y + dy;
    }
}

p: Point = Point { x: 3, y: 4 };
say(p.length());
p.move(1, 1);
say(p.x);
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["25", "4", "5"]


def test_bound_method_is_a_value():
    result = run_echo(
        """
class Point {
    new {
    x: int;
    y: int;
    }

    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }
}

p: Point = Point { x: 3, y: 4 };
bound: fn() -> int = p.length;
say(bound());
p.x = 0;
say(bound());
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["25", "16"]


def test_inline_method():
    result = run_echo(
        """
class Counter {
    new {
    n: int;
    }
    fn bump(this) -> int => this.n + 1;
}
c: Counter = Counter { n: 7 };
say(c.bump());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "8"


def test_unknown_method_is_e2704():
    result = run_echo(
        """
class Point {
    new {
    x: int;
    }
    fn length(this) -> int {
        return this.x;
    }
}
p: Point = Point { x: 1 };
say(p.missing());
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2704" in result.output


def test_method_arity_error():
    result = run_echo(
        """
class Point {
    new {
    x: int;
    }
    fn move(this, dx: int) -> void {
        this.x = this.x + dx;
    }
}
p: Point = Point { x: 1 };
p.move();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_this_must_be_first_and_untyped():
    result = run_echo(
        """
class Point {
    new {
    x: int;
    }
    fn bad(x: int) -> int {
        return x;
    }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_typed_this_is_rejected():
    result = run_echo(
        """
class Point {
    new {
    x: int;
    }
    fn bad(this: Point) -> int {
        return this.x;
    }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_formatter_prints_methods():
    formatted = format_source(
        """
class Point {
new {
x: int;
}
fn length(this) -> int {
return this.x;
}
}
"""
    )
    assert "new {" in formatted
    assert "fn length(this) -> int" in formatted
    assert "this.x" in formatted


def test_export_class_methods(tmp_path: Path):
    write_modules(
        tmp_path,
        {
            "geo.echo": """
                export class Point {
                    new {
                    x: int;
                    y: int;
                    }
                    fn length(this) -> int {
                        return this.x * this.x + this.y * this.y;
                    }
                }
            """,
            "app.echo": """
                import Point from "geo";
                p: Point = Point { x: 3, y: 4 };
                say(p.length());
            """,
        },
    )
    assert_success(run_entry(tmp_path), "25")
