from __future__ import annotations

from email.message import EmailMessage
from io import BytesIO
from pathlib import Path

from echo.runtime.host import Host
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


class _FakeResponse:
    def __init__(self, status: int, body: bytes, headers: dict[str, str] | None = None):
        self.status = status
        self.code = status
        self.headers = EmailMessage()
        for key, value in (headers or {"Content-Type": "text/plain"}).items():
            self.headers[key] = value
        self._body = BytesIO(body)

    def read(self) -> bytes:
        return self._body.read()

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_import_http_ok_from_std_http(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import httpOk from "std/http";
                import httpRedirect from "std/http";
                say(httpOk(200));
                say(httpOk(404));
                say(httpRedirect(302));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "true\nfalse\ntrue")


def test_import_http_get_from_std_http(tmp_path: Path, monkeypatch) -> None:
    def fake_open(request, timeout=30.0):
        assert request.get_method() == "GET"
        return _FakeResponse(200, b"pong", {"X-Test": "1"})

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import httpGet from "std/http";
                import httpOk from "std/http";
                resp: hash = httpGet("https://example.com/ping");
                say(resp["body"]);
                say(httpOk(resp));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "pong\ntrue")


def test_std_http_headers_and_or(tmp_path: Path, monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_open(request, timeout=30.0):
        seen["auth"] = request.get_header("Authorization")
        raise OSError("offline")

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import httpGetOr from "std/http";
                fallback: hash = { status: 0, body: "offline", headers: {} };
                resp: dynamic = httpGetOr(
                    "https://example.com/",
                    fallback,
                    { Authorization: "Bearer t" }
                );
                say(resp["body"]);
            """,
        },
    )
    assert_success(run_entry(tmp_path), "offline")
    assert seen["auth"] == "Bearer t"


def test_prelude_http_still_works_without_import(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                say(httpOk(201));
                say(httpRedirect(301));
            """,
        },
    )
    assert_success(run_entry(tmp_path), "true\ntrue")


def test_std_http_respects_allow_http(tmp_path: Path) -> None:
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import httpGet from "std/http";
                httpGet("https://example.com/");
            """,
        },
    )
    result = run_entry(tmp_path, host=Host(allow_http=False))
    assert_echo_error(result, "E2801")
