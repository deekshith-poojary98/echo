from pathlib import Path

from helpers import run_echo
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_use_name_retains_v021_behavior() -> None:
    result = run_echo(
        """
count: int = 1;
fn read() -> int {
    use count;
    return count;
}
say(read());
"""
    )
    assert_success(result, "1")


def test_use_mut_retains_v021_behavior() -> None:
    result = run_echo(
        """
count: int = 0;
fn bump() {
    use mut count;
    count = count + 1;
}
bump();
bump();
say(count);
"""
    )
    assert_success(result, "2")


def test_use_does_not_load_modules(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "math.echo": """
                export fn add(a: int, b: int) -> int {
                    return a + b;
                }
                say("math-loaded");
            """,
            "app.echo": """
                use math;
            """,
        },
    )
    result = run_entry(tmp_path)
    assert_echo_error(result)
    assert "math-loaded" not in result.output


def test_existing_programs_without_import_remain_unchanged(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "unused.echo": """
                export secret: int = 99;
                say("should-not-run");
            """,
            "app.echo": """
                count: int = 0;
                fn bump() {
                    use mut count;
                    count = count + 1;
                }
                bump();
                say(count);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "1")
