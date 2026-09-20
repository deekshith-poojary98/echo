from pathlib import Path

from echo.formatter import format_source
from echo.frontend.ast.nodes import ClassDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo
from modules.harness import assert_success, run_entry, write_modules


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_allows_type_method_without_this():
    declaration = parse_source(
        """
class Point {
    new { x: int; y: int; }
    fn origin() -> Point {
        return Point { x: 0, y: 0 };
    }
    fn length(this) -> int {
        return this.x;
    }
}
"""
    ).statements[0]
    assert isinstance(declaration, ClassDeclaration)
    assert declaration.methods[0].parameters == []
    assert declaration.methods[1].parameters[0].name == "this"


def test_type_method_call_and_value():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int;
    }

    fn origin() -> Point {
        return Point { x: 0, y: 0 };
    }

    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }
}

p: Point = Point.origin();
say(p.x);
say(p.y);
factory: fn() -> Point = Point.origin;
q: Point = factory();
say(Point.length(q));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["0", "0", "0"]


def test_type_method_with_args():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int;
    }

    fn of(x: int, y: int) -> Point {
        return Point { x: x, y: y };
    }
}

p: Point = Point.of(3, 4);
say(p.x);
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "4"]


def test_instance_call_of_type_method_is_e3213():
    result = run_echo(
        """
class Point {
    new { x: int; }
    fn origin() -> Point {
        return Point { x: 0 };
    }
}
p: Point = Point { x: 1 };
p.origin();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3213" in result.output


def test_instance_access_of_type_method_is_e3213():
    result = run_echo(
        """
class Point {
    new { x: int; }
    fn origin() -> Point {
        return Point { x: 0 };
    }
}
p: Point = Point { x: 1 };
f: fn() -> Point = p.origin;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3213" in result.output


def test_unbound_instance_method_still_works():
    result = run_echo(
        """
class Point {
    new { x: int; y: int; }
    fn origin() -> Point {
        return Point { x: 0, y: 0 };
    }
    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }
}
p: Point = Point { x: 3, y: 4 };
say(Point.length(p));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "25"


def test_export_type_method(tmp_path: Path):
    write_modules(
        tmp_path,
        {
            "geo.echo": """
                export class Point {
                    new {
                        x: int;
                        y: int;
                    }
                    fn origin() -> Point {
                        return Point { x: 0, y: 0 };
                    }
                }
            """,
            "app.echo": """
                import Point from "geo";
                p: Point = Point.origin();
                say(p.x);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "0")


def test_formatter_prints_type_method():
    formatted = format_source(
        """
class Point {
new { x: int; }
fn origin() -> Point {
return Point { x: 0 };
}
}
"""
    )
    assert "fn origin() -> Point" in formatted
    assert "this" not in formatted.split("fn origin")[1].split("{")[0]
