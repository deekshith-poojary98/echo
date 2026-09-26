from __future__ import annotations

from urllib.parse import unquote, urlparse
from urllib.request import url2pathname


def uri_to_path(uri: str) -> str | None:
    if not uri:
        return None
    if uri.startswith("file:"):
        parsed = urlparse(uri)
        path = url2pathname(unquote(parsed.path))
        # url2pathname on Unix keeps a leading slash; on Windows may add drive.
        return path or None
    return uri


def path_to_uri(path: str) -> str:
    from pathlib import Path

    return Path(path).expanduser().resolve().as_uri()


def echo_to_lsp_position(line: int, column: int) -> dict[str, int]:
    """Echo SourceLocation is 1-based; LSP Position is 0-based."""
    return {"line": max(line - 1, 0), "character": max(column - 1, 0)}


def lsp_to_echo_position(line: int, character: int) -> tuple[int, int]:
    return line + 1, character + 1
