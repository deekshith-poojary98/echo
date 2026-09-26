from pathlib import Path

from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_import_regex_from_std_re(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import regexMatch from "std/re";
                import regexFind from "std/re";
                import regexReplace from "std/re";
                import regexSplit from "std/re";
                say(regexMatch("abc123", "[0-9]+"));
                say(regexFind("a1b2", "[0-9]+"));
                say(regexReplace("a-b-c", "-", "_"));
                say(regexSplit("a,b,c", ","));
            """,
        },
    )
    assert_success(run_entry(tmp_path), 'true\n1\na_b_c\n["a", "b", "c"]')


def test_import_time_from_std_time(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import formatTime from "std/time";
                import parseTime from "std/time";
                import days from "std/time";
                import hours from "std/time";
                import minutes from "std/time";
                secs: int = parseTime("2020-01-02T03:04:05Z", "%Y-%m-%dT%H:%M:%SZ");
                say(formatTime(secs, "%Y-%m-%d"));
                say(days(1));
                say(hours(2));
                say(minutes(3));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "2020-01-02\n86400\n7200\n180")


def test_prelude_re_and_time_still_work(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                say(regexMatch("xy", "x."));
                say(minutes(1));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "true\n60")


def test_std_re_type_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import regexMatch from "std/re";
                regexMatch(1, "x");
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "E2850")


def test_std_time_type_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import formatTime from "std/time";
                formatTime("nope", "%Y");
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "E2851")
