from echo.formatter import format_source
from echo.frontend.ast.nodes import ClassDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_captures_implements():
    declaration = parse_source(
        """
interface Named {
    fn name(this) -> str;
}
class User implements Named {
    new { label: str; }
    fn name(this) -> str {
        return this.label;
    }
}
"""
    ).statements[1]
    assert isinstance(declaration, ClassDeclaration)
    assert declaration.implements == ["Named"]


def test_parser_multiple_implements():
    declaration = parse_source(
        """
interface A { fn a(this) -> int; }
interface B { fn b(this) -> int; }
class C implements A, B {
    fn a(this) -> int { return 1; }
    fn b(this) -> int { return 2; }
}
"""
    ).statements[2]
    assert isinstance(declaration, ClassDeclaration)
    assert declaration.implements == ["A", "B"]


def test_implements_ok_and_assignable():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}

class User implements Named {
    new {
        label: str;
    }

    fn name(this) -> str {
        return this.label;
    }
}

fn show(n: Named) {
    say(n.name());
}

u: User = User { label: "Ada" };
show(u);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_inference_still_works_without_implements():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
class User {
    new { label: str; }
    fn name(this) -> str {
        return this.label;
    }
}
n: Named = User { label: "Ada" };
say(n.name());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_missing_method_is_e3214():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
class User implements Named {
    new { id: int; }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3214" in result.output


def test_incompatible_signature_is_e3214():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
class User implements Named {
    new { label: str; }
    fn name(this) -> int {
        return 1;
    }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3214" in result.output


def test_unknown_interface_is_e3214():
    result = run_echo(
        """
class User implements Missing {
    new { id: int; }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3214" in result.output


def test_cannot_implement_a_class():
    result = run_echo(
        """
class Other { }
class User implements Other {
    new { id: int; }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3214" in result.output


def test_duplicate_implements_is_parse_error():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
class User implements Named, Named {
    new { label: str; }
    fn name(this) -> str {
        return this.label;
    }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_formatter_prints_implements():
    formatted = format_source(
        """
interface Named {
fn name(this) -> str;
}
class User implements Named {
new { label: str; }
fn name(this) -> str { return this.label; }
}
"""
    )
    assert "class User implements Named {" in formatted
