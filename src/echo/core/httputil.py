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


def _require_headers(value: object, method: str, location: SourceLocation | None) -> dict[str, str]:
    if not isinstance(value, dict):
        raise EchoTypeError(f"{method}() headers must be a hash", location, code="E2852")
    headers: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise EchoTypeError(f"{method}() header names must be strings", location, code="E2852")
        if not isinstance(item, str):
            raise EchoTypeError(f"{method}() header values must be strings", location, code="E2852")
        headers[key] = item
    return headers


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


def _status_code(value: object, method: str, location: SourceLocation | None) -> int:
    if isinstance(value, bool):
        raise EchoTypeError(f"{method}() status must be an int or response hash", location, code="E2852")
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        status = value.get("status")
        if isinstance(status, bool) or not isinstance(status, int):
            raise EchoTypeError(f"{method}() response hash needs an int status", location, code="E2852")
        return status
    raise EchoTypeError(f"{method}() status must be an int or response hash", location, code="E2852")


def http_ok(value: object, location: SourceLocation | None = None) -> bool:
    status = _status_code(value, "httpOk", location)
    return 200 <= status <= 299


def http_redirect(value: object, location: SourceLocation | None = None) -> bool:
    status = _status_code(value, "httpRedirect", location)
    return 300 <= status <= 399


def http_request(
    method: str,
    url: object,
    *,
    body: object | None = None,
    headers: object | None = None,
    location: SourceLocation | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: HttpOpener | None = None,
    builtin: str | None = None,
) -> dict[str, object]:
    name = builtin or ("httpGet" if method.upper() == "GET" else "httpPost")
    target = _require_url(url, name, location)
    request_headers = _require_headers(headers, name, location) if headers is not None else {}
    data: bytes | None = None
    if body is not None:
        text = _require_body(body, name, location)
        data = text.encode("utf-8")
        if not any(key.lower() == "content-type" for key in request_headers):
            request_headers = {**request_headers, "Content-Type": "text/plain; charset=utf-8"}
    request = Request(target, data=data, headers=request_headers, method=method.upper())
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
    headers: object | None = None,
    *,
    location: SourceLocation | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: HttpOpener | None = None,
    builtin: str = "httpGet",
) -> dict[str, object]:
    return http_request(
        "GET",
        url,
        headers=headers,
        location=location,
        timeout=timeout,
        opener=opener,
        builtin=builtin,
    )


def http_post(
    url: object,
    body: object,
    headers: object | None = None,
    *,
    location: SourceLocation | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: HttpOpener | None = None,
    builtin: str = "httpPost",
) -> dict[str, object]:
    return http_request(
        "POST",
        url,
        body=body,
        headers=headers,
        location=location,
        timeout=timeout,
        opener=opener,
        builtin=builtin,
    )
