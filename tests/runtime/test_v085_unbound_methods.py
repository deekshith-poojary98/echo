from pathlib import Path

from echo.formatter import format_source
from helpers import assert_no_python_leak, run_echo
from modules.harness import assert_success, run_entry, write_modules


def test_unbound_method_call():
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
say(Point.length(p));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "25"


def test_unbound_method_as_value():
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
raw: fn(Point) -> int = Point.length;
say(raw(p));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "25"


def test_bound_and_unbound_are_equivalent():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int;
    }

    fn move(this, dx: int, dy: int) -> void {
        this.x = this.x + dx;
        this.y = this.y + dy;
    }
}

p: Point = Point { x: 1, y: 2 };
p.move(1, 1);
Point.move(p, 1, 1);
say(p.x);
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "4"]


def test_unknown_unbound_method_is_e2704():
    result = run_echo(
        """
class Point {
    new { x: int; }
    fn length(this) -> int {
        return this.x;
    }
}
say(Point.missing);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2704" in result.output


def test_unbound_arity_mismatch():
    result = run_echo(
        """
class Point {
    new { x: int; }
    fn length(this) -> int {
        return this.x;
    }
}
p: Point = Point { x: 1 };
Point.length();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_unbound_wrong_receiver_type():
    result = run_echo(
        """
class Point {
    new { x: int; }
    fn length(this) -> int {
        return this.x;
    }
}
Point.length(1);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_shadowed_class_name_uses_instance_member():
    result = run_echo(
        """
class Point {
    new { x: int; }
    fn length(this) -> int {
        return this.x;
    }
}
Point: Point = Point { x: 9 };
say(Point.length());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "9"


def test_export_unbound_method(tmp_path: Path):
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
                say(Point.length(p));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "25")


def test_formatter_still_prints_methods():
    formatted = format_source(
        """
class Point {
new { x: int; }
fn length(this) -> int { return this.x; }
}
say(Point.length(Point { x: 1 }));
"""
    )
    assert "fn length(this) -> int" in formatted
    assert "Point.length" in formatted
