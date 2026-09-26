from __future__ import annotations

from email.message import Message
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from echo.errors import EchoRuntimeError, EchoTypeError, SourceLocation

HttpOpener = Callable[..., object]

DEFAULT_TIMEOUT_SECONDS = 30.0


def _require_url(value: object, method: str, location: SourceLocation | None) -> str:
    if not isinstance(value, str):
        raise EchoTypeError(f"{method}() url must be a string", location, code="E2852")
    if not value:
        raise EchoRuntimeError(f"{method}() url must not be empty", location, code="E2852")
    return value


def _require_body(value: object, method: str, location: SourceLocation | None) -> str:
    if not isinstance(value, str):
        raise EchoTypeError(f"{method}() body must be a string", location, code="E2852")
    return value


def _headers_to_hash(headers: Message) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in headers.items():
        name = str(key)
        text = str(value)
        if name in result:
            result[name] = f"{result[name]}, {text}"
        else:
            result[name] = text
    return result


def _read_response(response: object) -> dict[str, object]:
    status = int(getattr(response, "status", getattr(response, "code", 0)))
    header_map = getattr(response, "headers", None)
    headers = _headers_to_hash(header_map) if isinstance(header_map, Message) else {}
    raw = response.read()  # type: ignore[attr-defined]
    charset = "utf-8"
    if isinstance(header_map, Message):
        charset = header_map.get_content_charset() or "utf-8"
    if isinstance(raw, bytes):
        body = raw.decode(charset, errors="replace")
    else:
        body = str(raw)
    return {
        "status": status,
        "body": body,
        "headers": headers,
    }


def http_request(
    method: str,
    url: object,
    *,
    body: object | None = None,
    location: SourceLocation | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: HttpOpener | None = None,
) -> dict[str, object]:
    builtin = "httpGet" if method.upper() == "GET" else "httpPost"
    target = _require_url(url, builtin, location)
    data: bytes | None = None
    headers: dict[str, str] = {}
    if body is not None:
        text = _require_body(body, builtin, location)
        data = text.encode("utf-8")
        headers["Content-Type"] = "text/plain; charset=utf-8"
    request = Request(target, data=data, headers=headers, method=method.upper())
    open_url = opener or urlopen
    try:
        with open_url(request, timeout=timeout) as response:
            return _read_response(response)
    except HTTPError as exc:
        try:
            return _read_response(exc)
        finally:
            exc.close()
    except URLError as exc:
        reason = exc.reason if exc.reason is not None else exc
        raise EchoRuntimeError(f"http request failed: {reason}", location, code="E2852") from exc
    except TimeoutError as exc:
        raise EchoRuntimeError("http request timed out", location, code="E2852") from exc
    except OSError as exc:
        raise EchoRuntimeError(f"http request failed: {exc}", location, code="E2852") from exc
    except ValueError as exc:
        raise EchoRuntimeError(f"invalid url: {exc}", location, code="E2852") from exc


def http_get(
    url: object,
    *,
    location: SourceLocation | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: HttpOpener | None = None,
) -> dict[str, object]:
    return http_request("GET", url, location=location, timeout=timeout, opener=opener)


def http_post(
    url: object,
    body: object,
    *,
    location: SourceLocation | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: HttpOpener | None = None,
) -> dict[str, object]:
    return http_request("POST", url, body=body, location=location, timeout=timeout, opener=opener)
