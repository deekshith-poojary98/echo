from pathlib import Path

from echo.lsp.definition import definition_at
from echo.lsp.protocol import path_to_uri
from echo.lsp.server import exchange


def test_definition_local_function():
    source = "fn add(a: int, b: int) -> int {\n  return a + b;\n}\nsay(add(1, 2));\n"
    # Cursor on add in say(add(...)) — line index 3, character of 'a' in add
    locs = definition_at("file:///tmp/local.echo", source, 3, 4)
    assert len(locs) == 1
    assert locs[0]["range"]["start"]["line"] == 0


def test_definition_local_parameter(tmp_path):
    path = tmp_path / "fn.echo"
    source = "fn add(a: int, b: int) -> int {\n  return a + b;\n}\n"
    path.write_text(source, encoding="utf-8")
    uri = path_to_uri(str(path))
    # 'a' in return a + b (line index 1)
    locs = definition_at(uri, source, 1, 9)
    assert len(locs) == 1
    assert locs[0]["uri"] == uri
    assert locs[0]["range"]["start"]["line"] == 0
    assert locs[0]["range"]["start"]["character"] == 7  # parameter a


def test_definition_imported_symbol(tmp_path):
    (tmp_path / "math.echo").write_text(
        'export fn add(a: int, b: int) -> int { return a + b; }\n',
        encoding="utf-8",
    )
    app = 'import add from "math";\nsay(add(2, 3));\n'
    app_path = tmp_path / "app.echo"
    app_path.write_text(app, encoding="utf-8")
    uri = path_to_uri(str(app_path))
    locs = definition_at(uri, app, 1, 4)
    assert len(locs) == 1
    assert locs[0]["uri"] == path_to_uri(str(tmp_path / "math.echo"))
    assert locs[0]["range"]["start"]["line"] == 0
    # Should land on the name `add`, not the `export`/`fn` keyword.
    assert locs[0]["range"]["start"]["character"] == 10


def test_definition_builtin_returns_empty():
    source = "say(1);\n"
    assert definition_at("file:///tmp/b.echo", source, 0, 0) == []


def test_lsp_definition_roundtrip(tmp_path):
    (tmp_path / "math.echo").write_text(
        "export fn square(x: int) -> int { return x * x; }\n",
        encoding="utf-8",
    )
    app = 'import square from "math";\nsay(square(4));\n'
    app_path = tmp_path / "app.echo"
    app_path.write_text(app, encoding="utf-8")
    uri = path_to_uri(str(app_path))
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"capabilities": {}}},
        {"jsonrpc": "2.0", "method": "initialized", "params": {}},
        {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": uri,
                    "languageId": "echo",
                    "version": 1,
                    "text": app,
                }
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": 1, "character": 4},
            },
        },
        {"jsonrpc": "2.0", "id": 3, "method": "shutdown", "params": None},
        {"jsonrpc": "2.0", "method": "exit"},
    ]
    outbound = exchange(messages)
    init = next(m for m in outbound if m.get("id") == 1)
    assert init["result"]["capabilities"]["definitionProvider"] is True
    result = next(m for m in outbound if m.get("id") == 2)["result"]
    assert len(result) == 1
    assert result[0]["uri"] == path_to_uri(str(tmp_path / "math.echo"))
