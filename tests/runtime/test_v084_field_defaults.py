from pathlib import Path

from echo.formatter import format_source
from echo.frontend.ast.nodes import ClassDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo
from modules.harness import assert_success, run_entry, write_modules


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_captures_field_defaults():
    declaration = parse_source(
        """
class Point {
    new {
        x: int = 0;
        y: int = 0;
    }
}
"""
    ).statements[0]
    assert isinstance(declaration, ClassDeclaration)
    assert declaration.fields[0].default is not None
    assert declaration.fields[1].default is not None


def test_empty_construction_uses_defaults():
    result = run_echo(
        """
class Point {
    new {
        x: int = 0;
        y: int = 0;
    }
}
origin: Point = Point {};
say(origin.x);
say(origin.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["0", "0"]


def test_partial_construction_fills_omitted_defaults():
    result = run_echo(
        """
class Point {
    new {
        x: int = 0;
        y: int = 0;
    }
}
p: Point = Point { x: 3 };
say(p.x);
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "0"]


def test_explicit_field_overrides_default():
    result = run_echo(
        """
class Point {
    new {
        x: int = 0;
        y: int = 0;
    }
}
p: Point = Point { x: 3, y: 4 };
say(p.x);
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "4"]


def test_required_field_without_default_still_e3209():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int = 0;
    }
}
p: Point = Point { y: 1 };
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3209" in result.output


def test_extra_field_still_e3208():
    result = run_echo(
        """
class Point {
    new {
        x: int = 0;
    }
}
p: Point = Point { x: 1, z: 2 };
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3208" in result.output


def test_default_type_mismatch_is_rejected():
    result = run_echo(
        """
class Point {
    new {
        x: int = "no";
    }
}
p: Point = Point {};
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_default_expression_evaluated_at_construction():
    result = run_echo(
        """
n: int = 7;
class Box {
    new {
        value: int = n;
    }
}
a: Box = Box {};
n = 9;
b: Box = Box {};
say(a.value);
say(b.value);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["7", "9"]


def test_default_expression_uses_declaring_env_not_local_shadow():
    result = run_echo(
        """
n: int = 7;
class Box {
    new {
        value: int = n;
    }
}
fn make() {
    n: int = 0;
    box: Box = Box {};
    say(box.value);
}
make();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "7"


def test_imported_class_default_uses_declaring_module_variable(tmp_path: Path):
    write_modules(
        tmp_path,
        {
            "lib.echo": """
                DEFAULT_TIMEOUT: int = 30;
                export class Config {
                    new {
                        timeout: int = DEFAULT_TIMEOUT;
                    }
                }
            """,
            "app.echo": """
                import Config from "lib";
                c: Config = Config {};
                say(c.timeout);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "30")


def test_imported_class_default_ignores_importer_name_collision(tmp_path: Path):
    write_modules(
        tmp_path,
        {
            "lib.echo": """
                DEFAULT_TIMEOUT: int = 30;
                export class Config {
                    new {
                        timeout: int = DEFAULT_TIMEOUT;
                    }
                }
            """,
            "app.echo": """
                import Config from "lib";
                DEFAULT_TIMEOUT: int = 0;
                c: Config = Config {};
                say(c.timeout);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "30")


def test_formatter_prints_field_defaults():
    formatted = format_source(
        """
class Point {
new {
x: int = 0;
y: int;
}
}
"""
    )
    assert "x: int = 0;" in formatted
    assert "y: int;" in formatted
    assert "new {" in formatted
