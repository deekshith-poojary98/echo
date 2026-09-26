from pathlib import Path

from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_import_url_helpers_from_std_url(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import urlEncode from "std/url";
                import urlDecode from "std/url";
                import urlJoin from "std/url";
                import urlQuery from "std/url";
                say(urlEncode("a b"));
                say(urlDecode("a%20b"));
                say(urlJoin("https://example.com/api/", "../x"));
                say(urlQuery({ q: "hi", n: "1" }));
            """,
        },
    )
    assert_success(
        run_entry(tmp_path),
        "a%20b\na b\nhttps://example.com/x\nq=hi&n=1",
    )


def test_import_base64_from_std_base64(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import base64Encode from "std/base64";
                import base64Decode from "std/base64";
                encoded: str = base64Encode("Echo");
                say(encoded);
                say(base64Decode(encoded));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "RWNobw==\nEcho")


def test_prelude_url_and_base64_still_work(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                say(urlEncode("x y"));
                say(base64Encode("ab"));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "x%20y\nYWI=")


def test_std_url_type_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import urlEncode from "std/url";
                urlEncode(1);
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "E2853")


def test_std_base64_type_error(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import base64Decode from "std/base64";
                base64Decode(1);
            """,
        },
    )
    assert_echo_error(run_entry(tmp_path), "E2854")
