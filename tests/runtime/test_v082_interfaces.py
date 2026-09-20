from pathlib import Path

from echo.formatter import format_source
from echo.frontend.ast.nodes import InterfaceDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import assert_no_python_leak, run_echo
from modules.harness import assert_success, run_entry, write_modules


def parse_source(source: str):
    return Parser(Lexer().tokenize(source)).parse()


def test_parser_builds_interface():
    declaration = parse_source(
        """
interface Named {
    fn name(this) -> str;
}
"""
    ).statements[0]
    assert isinstance(declaration, InterfaceDeclaration)
    assert declaration.name == "Named"
    assert len(declaration.methods) == 1
    assert declaration.methods[0].name == "name"
    assert declaration.methods[0].parameters[0].name == "this"


def test_class_instance_satisfies_interface():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}

class User {
    new {
    id: int;
    label: str;
    }

    fn name(this) -> str {
        return this.label;
    }
}

fn show(n: Named) {
    say(n.name());
}

u: User = User { id: 1, label: "Ada" };
show(u);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_interface_typed_binding():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
class User {
    new {
    label: str;
    }
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


def test_missing_method_rejects_interface_assign():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
class User {
    new {
    id: int;
    }
}
n: Named = User { id: 1 };
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_interface_to_interface_subset():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
interface Labeled {
    fn name(this) -> str;
    fn label(this) -> str;
}
class User {
    new {
    text: str;
    }
    fn name(this) -> str {
        return this.text;
    }
    fn label(this) -> str {
        return this.text;
    }
}
full: Labeled = User { text: "Ada" };
narrow: Named = full;
say(narrow.name());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_switch_on_interface_needs_else():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
class User {
    new {
    label: str;
    }
    fn name(this) -> str {
        return this.label;
    }
}
n: Named = User { label: "Ada" };
switch n {
    Named { say("named"); }
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3210" in result.output


def test_bound_method_through_interface():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}
class User {
    new {
    label: str;
    }
    fn name(this) -> str {
        return this.label;
    }
}
n: Named = User { label: "Ada" };
f: fn() -> str = n.name;
say(f());
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_formatter_prints_interface():
    formatted = format_source(
        """
interface Named {
fn name(this) -> str;
}
"""
    )
    assert "interface Named {" in formatted
    assert "fn name(this) -> str;" in formatted


def test_export_interface(tmp_path: Path):
    write_modules(
        tmp_path,
        {
            "api.echo": """
                export interface Named {
                    fn name(this) -> str;
                }
                export class User {
                    new {
                    label: str;
                    }
                    fn name(this) -> str {
                        return this.label;
                    }
                }
            """,
            "app.echo": """
                import Named from "api";
                import User from "api";
                fn show(n: Named) {
                    say(n.name());
                }
                show(User { label: "Ada" });
            """,
        },
    )
    assert_success(run_entry(tmp_path), "Ada")
