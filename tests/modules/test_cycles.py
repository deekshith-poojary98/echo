from pathlib import Path

from modules.harness import assert_echo_error, run_entry, write_modules


def test_direct_cycle_is_rejected(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "a.echo": """
                import x from "b";
                export y: int = 1;
            """,
            "b.echo": """
                import y from "a";
                export x: int = 2;
            """,
            "app.echo": """
                import y from "a";
                say(y);
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path))


def test_indirect_cycle_is_rejected(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "a.echo": """
                import mid from "b";
                export start: int = 1;
            """,
            "b.echo": """
                import finish from "c";
                export mid: int = 2;
            """,
            "c.echo": """
                import start from "a";
                export finish: int = 3;
            """,
            "app.echo": """
                import start from "a";
                say(start);
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path))


def test_longer_dependency_cycle_is_rejected(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "one.echo": """
                import two from "two";
                export one: int = 1;
            """,
            "two.echo": """
                import three from "three";
                export two: int = 2;
            """,
            "three.echo": """
                import four from "four";
                export three: int = 3;
            """,
            "four.echo": """
                import one from "one";
                export four: int = 4;
            """,
            "app.echo": """
                import one from "one";
                say(one);
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path))


def test_no_partially_initialized_module_is_exposed(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "a.echo": """
                import x from "b";
                export ready: int = 1;
                say("a-ran");
            """,
            "b.echo": """
                import ready from "a";
                export x: int = ready;
                say("b-ran");
            """,
            "app.echo": """
                import ready from "a";
                say(ready);
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result)
    assert "a-ran" not in result.output
    assert "b-ran" not in result.output


def test_cycle_error_identifies_the_dependency_problem(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "alpha.echo": """
                import beta_value from "beta";
                export alpha_value: int = 1;
            """,
            "beta.echo": """
                import alpha_value from "alpha";
                export beta_value: int = 2;
            """,
            "app.echo": """
                import alpha_value from "alpha";
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result)
    text = result.output.lower()
    assert "alpha" in text or "beta" in text
