from pathlib import Path

from echo.formatter import format_source
from echo.frontend.ast.nodes import ClassConstruction, ClassDeclaration, MemberAssignment
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_class_and_construction():
    program = parse_source(
        """
class Point {
    new {
    x: int;
    y: int;
    }
}
p: Point = Point { x: 3, y: 4 };
p.x = 10;
"""
    )
    declaration = program.statements[0]
    assert isinstance(declaration, ClassDeclaration)
    assert declaration.name == "Point"
    assert len(declaration.fields) == 2
    binding = program.statements[1]
    assert binding.declared_type.name == "Point"
    assert isinstance(binding.initializer, ClassConstruction)
    assert binding.initializer.class_name == "Point"
    assert isinstance(program.statements[2], MemberAssignment)


def test_construct_read_assign_and_type_name():
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
p.x = 10;
say(p.x);
say(type(p));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "10", "Point"]


def test_empty_class_is_nominal_tag():
    result = run_echo(
        """
class Marker { }
m: Marker = Marker {};
say(type(m));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Marker"


def test_construction_rejects_extra_field_with_e3208():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
p: Point = Point { x: 1, y: 2, z: 3 };
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3208" in result.output


def test_construction_rejects_missing_field_with_e3209():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
p: Point = Point { x: 1 };
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3209" in result.output


def test_exact_hash_is_not_assignable_to_class():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
h: exact { x: int, y: int } = { x: 1, y: 2 };
p: Point = h;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_class_is_not_assignable_to_exact_hash():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
p: Point = Point { x: 1, y: 2 };
h: exact { x: int, y: int } = p;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_unknown_field_is_e2704():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
p: Point = Point { x: 1, y: 2 };
say(p.z);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2704" in result.output


def test_equality_is_field_wise():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
a: Point = Point { x: 1, y: 2 };
b: Point = Point { x: 1, y: 2 };
c: Point = Point { x: 9, y: 2 };
say(a == b);
say(a == c);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["true", "false"]


def test_destructure_class_as_hash_shaped():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
p: Point = Point { x: 3, y: 4 };
{ x: int, y: int } = p;
say(x);
say(y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "4"]


def test_const_instance_rejects_field_assign():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
const p: Point = Point { x: 1, y: 2 };
p.x = 9;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3202" in result.output


def test_frozen_instance_via_other_name_is_e3203():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
const locked: Point = Point { x: 1, y: 2 };
alias: Point = locked;
alias.x = 9;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3203" in result.output


def test_switch_type_arm_matches_class():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
v: Point | int = Point { x: 1, y: 2 };
switch v {
    Point { say("point"); }
    int { say("int"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "point"


def test_switch_type_arm_binds_class():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
p: Point = Point { x: 7, y: 8 };
switch p {
    Point pt { say(pt.x); }
    else { say("no"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "7"


def test_union_with_class():
    result = run_echo(
        """
class Point { new { x: int; y: int; }}
v: Point | str = Point { x: 1, y: 2 };
say(type(v));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Point"


def test_formatter_prints_class():
    formatted = format_source(
        """
class Point {
new {
x: int;
y: int;
}
}
p: Point = Point { x: 3, y: 4 };
p.x = 10;
"""
    )
    assert "class Point {" in formatted
    assert "new {" in formatted
    assert "x: int;" in formatted
    assert "Point {x: 3, y: 4}" in formatted or "Point { x: 3, y: 4 }" in formatted
    assert "p.x = 10;" in formatted


def test_export_class_can_be_imported(tmp_path: Path):
    write_modules(
        tmp_path,
        {
            "geo.echo": """
                export class Point {
                    new {
                    x: int;
                    y: int;
                    }
                }
            """,
            "app.echo": """
                import Point from "geo";
                p: Point = Point { x: 3, y: 4 };
                say(p.x);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "3")


def test_private_class_cannot_be_imported(tmp_path: Path):
    write_modules(
        tmp_path,
        {
            "geo.echo": """
                class Point {
                    new {
                    x: int;
                    y: int;
                    }
                }
            """,
            "app.echo": """
                import Point from "geo";
                p: Point = Point { x: 1, y: 2 };
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result, "Point")
