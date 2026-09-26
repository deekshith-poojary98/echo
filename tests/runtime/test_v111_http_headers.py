from __future__ import annotations

from email.message import EmailMessage
from io import BytesIO
from urllib.error import URLError

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


def test_http_get_sends_request_headers(monkeypatch):
    seen: dict[str, object] = {}

    def fake_open(request, timeout=30.0):
        seen["auth"] = request.get_header("Authorization")
        return _FakeResponse(200, b"ok")

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    result = run_echo(
        """
resp: hash = httpGet("https://example.com/", { Authorization: "Bearer t" });
say(resp["status"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "200"
    assert seen["auth"] == "Bearer t"


def test_http_post_custom_content_type(monkeypatch):
    seen: dict[str, object] = {}

    def fake_open(request, timeout=30.0):
        seen["content_type"] = request.get_header("Content-type")
        seen["body"] = request.data
        return _FakeResponse(200, b"ok")

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    result = run_echo(
        """
httpPost("https://example.com/", "{\\"a\\":1}", { "Content-Type": "application/json" });
"""
    )
    assert result.exit_code == 0, result.output
    assert seen["content_type"] == "application/json"
    assert seen["body"] == b'{"a":1}'


def test_http_ok_and_redirect_helpers(monkeypatch):
    monkeypatch.setattr(
        "echo.core.httputil.urlopen",
        lambda request, timeout=30.0: _FakeResponse(200, b"ok"),
    )
    result = run_echo(
        """
resp: hash = httpGet("https://example.com/");
say(httpOk(resp));
say(httpRedirect(resp));
say(httpOk(302));
say(httpRedirect(302));
say(resp.httpOk());
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["true", "false", "false", "true", "true"]


def test_http_get_or_returns_fallback_on_network_error(monkeypatch):
    def fake_open(request, timeout=30.0):
        raise URLError("connection refused")

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    result = run_echo(
        """
resp: dynamic = httpGetOr("https://example.com/", { status: 0, body: "offline", headers: {} });
say(resp["body"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "offline"


def test_http_get_or_returns_response_on_success(monkeypatch):
    monkeypatch.setattr(
        "echo.core.httputil.urlopen",
        lambda request, timeout=30.0: _FakeResponse(200, b"live"),
    )
    result = run_echo(
        """
resp: dynamic = httpGetOr("https://example.com/", { status: 0, body: "offline", headers: {} });
say(resp["body"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "live"


def test_http_post_or_with_headers(monkeypatch):
    seen: dict[str, object] = {}

    def fake_open(request, timeout=30.0):
        seen["auth"] = request.get_header("Authorization")
        return _FakeResponse(201, b"created")

    monkeypatch.setattr("echo.core.httputil.urlopen", fake_open)
    result = run_echo(
        """
resp: dynamic = httpPostOr(
    "https://example.com/items",
    "x",
    { status: 0, body: "offline", headers: {} },
    { Authorization: "tok" }
);
say(resp["status"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "201"
    assert seen["auth"] == "tok"


def test_http_get_or_denied_still_aborts():
    result = run_echo(
        'httpGetOr("https://example.com/", null);\n',
        host=Host(allow_http=False),
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2801" in result.output


def test_http_get_or_bad_headers_type_still_aborts(monkeypatch):
    monkeypatch.setattr(
        "echo.core.httputil.urlopen",
        lambda request, timeout=30.0: _FakeResponse(200, b"ok"),
    )
    result = run_echo('httpGetOr("https://example.com/", null, "nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2852" in result.output


def test_http_ok_bad_type():
    result = run_echo('httpOk("nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2852" in result.output
