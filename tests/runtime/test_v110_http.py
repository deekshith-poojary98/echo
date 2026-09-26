from __future__ import annotations

from email.message import EmailMessage
from io import BytesIO

from echo.core.httputil import http_get, http_post
from echo.errors import EchoRuntimeError, EchoTypeError
from echo.runtime.host import Host
from helpers import assert_no_python_leak, run_echo


class _FakeResponse:
    def __init__(self, status: int, body: bytes, headers: dict[str, str] | None = None):
        self.status = status
        self.code = status
        self.headers = EmailMessage()
        for key, value in (headers or {"Content-Type": "text/plain; charset=utf-8"}).items():
            self.headers[key] = value
        self._body = BytesIO(body)

    def read(self) -> bytes:
        return self._body.read()

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_http_get_returns_status_body_headers(monkeypatch):
    def fake_open(request, timeout=30.0):
        assert request.get_method() == "GET"
        assert request.full_url == "https://example.com/ping"
        return _FakeResponse(200, b"pong", {"Content-Type": "text/plain", "X-Test": "1"})

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    result = run_echo(
        """
resp: hash = httpGet("https://example.com/ping");
say(resp["status"]);
say(resp["body"]);
say(resp["headers"]["X-Test"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["200", "pong", "1"]


def test_http_post_sends_body(monkeypatch):
    seen: dict[str, object] = {}

    def fake_open(request, timeout=30.0):
        seen["method"] = request.get_method()
        seen["url"] = request.full_url
        seen["body"] = request.data
        seen["content_type"] = request.get_header("Content-type")
        return _FakeResponse(201, b"created")

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    result = run_echo(
        """
resp: hash = httpPost("https://example.com/items", "hello");
say(resp["status"]);
say(resp["body"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["201", "created"]
    assert seen["method"] == "POST"
    assert seen["url"] == "https://example.com/items"
    assert seen["body"] == b"hello"
    assert "text/plain" in str(seen["content_type"])


def test_http_get_method_form(monkeypatch):
    monkeypatch.setattr(
        "echo.core.httputil.urlopen",
        lambda request, timeout=30.0: _FakeResponse(200, b"ok"),
    )
    result = run_echo('resp: hash = "https://example.com/".httpGet();\nsay(resp["body"]);\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "ok"


def test_http_non_2xx_still_returns_hash(monkeypatch):
    from urllib.error import HTTPError

    def fake_open(request, timeout=30.0):
        raise HTTPError(
            request.full_url,
            404,
            "Not Found",
            EmailMessage(),
            BytesIO(b"missing"),
        )

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    result = run_echo(
        """
resp: hash = httpGet("https://example.com/missing");
say(resp["status"]);
say(resp["body"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["404", "missing"]


def test_http_denied_on_restricted_host():
    result = run_echo('httpGet("https://example.com/");\n', host=Host(allow_http=False))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2801" in result.output


def test_http_post_denied_on_restricted_host():
    result = run_echo('httpPost("https://example.com/", "x");\n', host=Host(allow_http=False))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2801" in result.output


def test_http_get_bad_url_type():
    result = run_echo("httpGet(1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2852" in result.output


def test_http_network_failure_is_e2852(monkeypatch):
    from urllib.error import URLError

    def fake_open(request, timeout=30.0):
        raise URLError("connection refused")

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    result = run_echo('httpGet("https://example.com/");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2852" in result.output


def test_httputil_direct_rejects_non_string_body():
    try:
        http_post("https://example.com/", 1)
        raise AssertionError("expected EchoTypeError")
    except EchoTypeError as exc:
        assert exc.code == "E2852"


def test_httputil_empty_url_aborts():
    try:
        http_get("")
        raise AssertionError("expected EchoRuntimeError")
    except EchoRuntimeError as exc:
        assert exc.code == "E2852"


def test_playground_worker_denies_http():
    worker = ( __import__("pathlib").Path(__file__).resolve().parents[2]
        / "docs"
        / "public"
        / "echo-playground-worker.js"
    ).read_text(encoding="utf-8")
    assert "allow_http=False" in worker
