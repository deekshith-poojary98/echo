from textwrap import dedent

from echo.errors import SemanticError
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.semantics.analyzer import SemanticAnalyzer
from echo.semantics.symbols import SymbolKind


def parse_source(source: str):
    return Parser(Lexer().tokenize(dedent(source).strip() + "\n")).parse()


def analyze_modules(sources: dict[str, str]):
    programs = {name: parse_source(source) for name, source in sources.items()}
    return SemanticAnalyzer().analyze_modules(programs)


def analyze_one(source: str):
    return analyze_modules({"module": source})["module"]


def assert_semantic_error(sources: dict[str, str] | str, *needles: str) -> None:
    try:
        if isinstance(sources, str):
            analyze_one(sources)
        else:
            analyze_modules(sources)
        assert False, "expected SemanticError"
    except SemanticError as exc:
        text = str(exc).lower()
        for needle in needles:
            assert needle.lower() in text, f"{needle!r} not in {exc}"


MATH_ADD = """
    export fn add(a: int, b: int) -> int {
        return a + b;
    }
"""


def test_exported_function_exists():
    symbols = analyze_one(MATH_ADD)
    assert "add" in symbols.exports
    assert symbols.exports["add"].kind == SymbolKind.FUNCTION
    assert "add" not in symbols.private


def test_exported_variable_exists():
    symbols = analyze_one("export x: int = 10;")
    assert "x" in symbols.exports
    assert symbols.exports["x"].kind == SymbolKind.VARIABLE
    assert "x" not in symbols.private


def test_private_declaration_is_not_exported():
    symbols = analyze_one(
        """
        export fn add(a: int, b: int) -> int {
            return a + b;
        }
        x: int = 10;
        """
    )
    assert "x" in symbols.private
    assert "x" not in symbols.exports
    assert "add" in symbols.exports
    assert "add" not in symbols.private


def test_export_missing_name_is_an_error():
    assert_semantic_error("export doesNotExist;", "doesNotExist")


def test_export_existing_declaration():
    symbols = analyze_one(
        """
        fn add(a: int, b: int) -> int {
            return a + b;
        }
        export add;
        """
    )
    assert "add" in symbols.exports
    assert "add" not in symbols.private
    assert len([name for name in (*symbols.exports, *symbols.private) if name == "add"]) == 1


def test_import_exported_function():
    symbols = analyze_modules(
        {
            "math": MATH_ADD,
            "app": """
                import add from "math";
            """,
        }
    )
    imported = symbols["app"].imports["add"]
    assert imported.kind == SymbolKind.FUNCTION
    assert imported.mutable is False
    assert imported.imported is True
    assert "add" not in symbols["app"].private
    assert "add" not in symbols["app"].exports
    assert "add" in symbols["math"].exports


def test_import_exported_variable():
    symbols = analyze_modules(
        {
            "config": "export x: int = 10;",
            "app": 'import x from "config";',
        }
    )
    imported = symbols["app"].imports["x"]
    assert imported.kind == SymbolKind.VARIABLE
    assert imported.mutable is False
    assert imported.imported is True


def test_import_private_name_is_an_error():
    assert_semantic_error(
        {
            "math": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                fn subtract(a: int, b: int) -> int {
                    return a - b;
                }
            """,
            "app": 'import subtract from "math";',
        },
        "subtract",
        "math",
    )


def test_import_nonexistent_name_is_an_error():
    assert_semantic_error(
        {
            "math": MATH_ADD,
            "app": 'import missing from "math";',
        },
        "missing",
        "math",
    )


def test_private_and_missing_imports_are_distinct():
    try:
        analyze_modules(
            {
                "math": """
                    fn secret() -> int {
                        return 1;
                    }
                """,
                "app": 'import secret from "math";',
            }
        )
        assert False, "expected SemanticError"
    except SemanticError as private_error:
        private_text = str(private_error).lower()

    try:
        analyze_modules(
            {
                "math": """
                    fn secret() -> int {
                        return 1;
                    }
                """,
                "app": 'import absent from "math";',
            }
        )
        assert False, "expected SemanticError"
    except SemanticError as missing_error:
        missing_text = str(missing_error).lower()

    assert "secret" in private_text
    assert "absent" in missing_text
    assert private_text != missing_text


def test_multiple_imports_bind_only_selected_names():
    symbols = analyze_modules(
        {
            "math": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                export fn multiply(a: int, b: int) -> int {
                    return a * b;
                }
                export pi: int = 3;
            """,
            "app": """
                import add from "math";
                import pi from "math";
            """,
        }
    )
    assert set(symbols["app"].imports) == {"add", "pi"}
    assert "multiply" not in symbols["app"].imports
    assert "multiply" not in symbols["app"].private


def test_imported_name_collision_is_an_error():
    assert_semantic_error(
        {
            "math": "export x: int = 1;",
            "app": """
                x: int = 10;
                import x from "math";
            """,
        },
        "x",
    )


def test_duplicate_import_of_same_name_is_a_collision():
    assert_semantic_error(
        {
            "math": "export x: int = 1;",
            "other": "export x: int = 2;",
            "app": """
                import x from "math";
                import x from "other";
            """,
        },
        "x",
    )


def test_imported_name_cannot_be_assigned():
    assert_semantic_error(
        {
            "math": MATH_ADD,
            "app": """
                import add from "math";
                add = 1;
            """,
        },
        "add",
    )


def test_imported_name_cannot_be_redeclared():
    assert_semantic_error(
        {
            "math": MATH_ADD,
            "app": """
                import add from "math";
                add: int = 10;
            """,
        },
        "add",
    )


def test_use_mut_cannot_capture_imported_binding():
    assert_semantic_error(
        {
            "other": "export count: int = 0;",
            "app": """
                import count from "other";
                fn foo() {
                    use mut count;
                }
            """,
        },
        "count",
    )


def test_same_module_use_mut_remains_valid():
    symbols = analyze_one(
        """
        count: int = 0;
        fn counter() {
            use mut count;
            count = count + 1;
        }
        """
    )
    assert "count" in symbols.private
    assert symbols.private["count"].imported is False


def test_export_function_is_one_symbol():
    symbols = analyze_one(MATH_ADD)
    assert list(symbols.exports) == ["add"]
    assert symbols.exports["add"].kind == SymbolKind.FUNCTION
    assert symbols.exports["add"].param_names == ["a", "b"]


def test_import_plus_local_declarations():
    symbols = analyze_modules(
        {
            "math": MATH_ADD,
            "app": """
                import add from "math";
                label: str = "ok";
            """,
        }
    )
    assert "add" in symbols["app"].imports
    assert "label" in symbols["app"].private
    assert "label" not in symbols["app"].imports


def test_import_plus_nested_functions():
    analyze_modules(
        {
            "math": MATH_ADD,
            "app": """
                import add from "math";
                fn outer() -> int {
                    fn inner() -> int {
                        return add(1, 2);
                    }
                    return inner();
                }
            """,
        }
    )


def test_diamond_graph_imports():
    symbols = analyze_modules(
        {
            "common": "export value: int = 1;",
            "left": """
                import value from "common";
                export left_value: int = 2;
            """,
            "right": """
                import value from "common";
                export right_value: int = 3;
            """,
            "app": """
                import left_value from "left";
                import right_value from "right";
            """,
        }
    )
    assert "value" in symbols["common"].exports
    assert "value" in symbols["left"].imports
    assert "value" in symbols["right"].imports
    assert set(symbols["app"].imports) == {"left_value", "right_value"}
    assert "value" not in symbols["app"].imports
