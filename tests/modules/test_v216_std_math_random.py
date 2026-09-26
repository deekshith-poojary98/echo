from pathlib import Path

from echo.runtime.host import Host
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_import_math_from_std_math(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import abs from "std/math";
                import floor from "std/math";
                import ceil from "std/math";
                import min from "std/math";
                import max from "std/math";
                say(abs(-3));
                say(floor(3.2));
                say(ceil(3.2));
                say(min(2, 5));
                say(max(2, 5));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "3\n3\n4\n2\n5")


def test_import_random_from_std_random(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import random from "std/random";
                import randomInt from "std/random";
                n: float = random();
                say(n >= 0.0);
                say(n < 1.0);
                say(randomInt(1, 1));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "true\ntrue\n1")


def test_import_now_wait_from_std_time(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import now from "std/time";
                import wait from "std/time";
                import minutes from "std/time";
                stamp: int = now();
                wait(0);
                say(stamp > 0);
                say(minutes(1));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "true\n60")


def test_import_run_from_std_os(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import run from "std/os";
                result: hash = run("true", []);
                say(result["code"]);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "0")


def test_prelude_math_random_time_os_still_work(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                say(abs(-4));
                say(randomInt(7, 7));
                say(type(now()));
                say(minutes(1));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "4\n7\nint\n60")


def test_require_std_hides_math_and_import_works(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import abs from "std/math";
                say(abs(-9));
            """,
        },
    )
    assert_success(run_entry(tmp_path, host=Host(require_std=True)), "9")


def test_require_std_hides_abs_prelude() -> None:
    from helpers import run_echo

    result = run_echo("say(abs(-1));\n", host=Host(require_std=True))
    assert result.exit_code == 1
    assert "abs" in result.output.lower() or "not defined" in result.output.lower() or "E200" in result.output


def test_std_os_run_respects_allow_run(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import run from "std/os";
                run("true", []);
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path, host=Host(allow_run=False)), "E2801")
