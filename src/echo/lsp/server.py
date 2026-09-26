from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import BinaryIO

from echo import __version__
from echo.lsp.diagnostics import collect_diagnostics
from echo.lsp.hover import hover_at
from echo.runtime.host import Host


@dataclass
class LspServer:
    """Minimal stdio JSON-RPC language server (initialize, diagnostics, hover)."""

    stdin: BinaryIO
    stdout: BinaryIO
    host: Host = field(default_factory=Host)
    documents: dict[str, str] = field(default_factory=dict)
    _shutdown: bool = False
    _exit_code: int = 0

    def run(self) -> int:
        while True:
            message = self._read_message()
            if message is None:
                return self._exit_code
            self._dispatch(message)
            if message.get("method") == "exit":
                return self._exit_code

    def _read_message(self) -> dict | None:
        headers: dict[str, str] = {}
        while True:
            line = self.stdin.readline()
            if not line:
                return None
            if line in (b"\r\n", b"\n"):
                break
            text = line.decode("utf-8", errors="replace").strip()
            if ":" in text:
                key, value = text.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        length = int(headers.get("content-length", "0"))
        if length <= 0:
            return None
        body = self.stdin.read(length)
        if not body:
            return None
        return json.loads(body.decode("utf-8"))

    def _write_message(self, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        header = f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii")
        self.stdout.write(header + raw)
        self.stdout.flush()

    def _reply(self, request_id: object, result: object) -> None:
        self._write_message({"jsonrpc": "2.0", "id": request_id, "result": result})

    def _notify(self, method: str, params: dict) -> None:
        self._write_message({"jsonrpc": "2.0", "method": method, "params": params})

    def _dispatch(self, message: dict) -> None:
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            self._reply(
                request_id,
                {
                    "capabilities": {
                        "textDocumentSync": {
                            "openClose": True,
                            "change": 1,  # Full
                        },
                        "hoverProvider": True,
                    },
                    "serverInfo": {"name": "echo-lsp", "version": __version__},
                },
            )
            return
        if method == "initialized":
            return
        if method == "shutdown":
            self._shutdown = True
            self._reply(request_id, None)
            return
        if method == "exit":
            self._exit_code = 0 if self._shutdown else 1
            return
        if method == "textDocument/didOpen":
            self._did_open(params)
            return
        if method == "textDocument/didChange":
            self._did_change(params)
            return
        if method == "textDocument/didClose":
            self._did_close(params)
            return
        if method == "textDocument/hover":
            self._hover(request_id, params)
            return
        if request_id is not None:
            self._write_message(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            )

    def _publish(self, uri: str, text: str) -> None:
        diagnostics = collect_diagnostics(uri, text, host=self.host)
        self._notify(
            "textDocument/publishDiagnostics",
            {"uri": uri, "diagnostics": diagnostics},
        )

    def _did_open(self, params: dict) -> None:
        doc = params.get("textDocument") or {}
        uri = doc.get("uri") or ""
        text = doc.get("text") or ""
        self.documents[uri] = text
        self._publish(uri, text)

    def _did_change(self, params: dict) -> None:
        doc = params.get("textDocument") or {}
        uri = doc.get("uri") or ""
        changes = params.get("contentChanges") or []
        if not changes:
            return
        # Full document sync only.
        text = changes[-1].get("text")
        if text is None:
            return
        self.documents[uri] = text
        self._publish(uri, text)

    def _did_close(self, params: dict) -> None:
        doc = params.get("textDocument") or {}
        uri = doc.get("uri") or ""
        self.documents.pop(uri, None)
        self._notify("textDocument/publishDiagnostics", {"uri": uri, "diagnostics": []})

    def _hover(self, request_id: object, params: dict) -> None:
        doc = params.get("textDocument") or {}
        uri = doc.get("uri") or ""
        position = params.get("position") or {}
        text = self.documents.get(uri, "")
        result = hover_at(
            uri,
            text,
            int(position.get("line", 0)),
            int(position.get("character", 0)),
        )
        self._reply(request_id, result)


def run_stdio(
    *,
    stdin: BinaryIO | None = None,
    stdout: BinaryIO | None = None,
    host: Host | None = None,
) -> int:
    server = LspServer(
        stdin=stdin or sys.stdin.buffer,
        stdout=stdout or sys.stdout.buffer,
        host=host or Host(),
    )
    return server.run()


def exchange(
    messages: list[dict],
    *,
    host: Host | None = None,
) -> list[dict]:
    """Drive the server with in-memory messages; return all outbound payloads (tests)."""
    from io import BytesIO

    def encode(msg: dict) -> bytes:
        raw = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        return f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw

    inbound = b"".join(encode(message) for message in messages)
    # Always end with exit so the loop terminates.
    if not messages or messages[-1].get("method") != "exit":
        inbound += encode({"jsonrpc": "2.0", "method": "exit"})

    stdin = BytesIO(inbound)
    stdout = BytesIO()
    server = LspServer(stdin=stdin, stdout=stdout, host=host or Host())
    server.run()
    return _decode_stream(stdout.getvalue())


def _decode_stream(data: bytes) -> list[dict]:
    messages: list[dict] = []
    offset = 0
    while offset < len(data):
        header_end = data.find(b"\r\n\r\n", offset)
        if header_end < 0:
            break
        header = data[offset:header_end].decode("ascii", errors="replace")
        length = 0
        for line in header.split("\r\n"):
            if line.lower().startswith("content-length:"):
                length = int(line.split(":", 1)[1].strip())
        body_start = header_end + 4
        body = data[body_start : body_start + length]
        messages.append(json.loads(body.decode("utf-8")))
        offset = body_start + length
    return messages
