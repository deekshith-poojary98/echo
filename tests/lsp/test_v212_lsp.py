from echo.lsp.diagnostics import collect_diagnostics
from echo.lsp.hover import hover_at
from echo.lsp.server import exchange


def test_diagnostics_clean_program():
    diags = collect_diagnostics("file:///tmp/ok.echo", "say(1);\n")
    assert diags == []


def test_diagnostics_semantic_error():
    diags = collect_diagnostics("file:///tmp/bad.echo", "say(missing);\n")
    assert len(diags) == 1
    assert diags[0]["severity"] == 1
    assert diags[0]["source"] == "echo"
    assert "missing" in diags[0]["message"].lower() or "E" in str(diags[0].get("code", ""))


def test_diagnostics_syntax_error():
    diags = collect_diagnostics("file:///tmp/syn.echo", "fn {\n")
    assert len(diags) == 1
    assert diags[0]["severity"] == 1


def test_hover_builtin_say():
    source = "say(1);\n"
    # 'say' starts at line 0 col 0 in LSP
    result = hover_at("file:///tmp/h.echo", source, 0, 0)
    assert result is not None
    value = result["contents"]["value"]
    assert "say" in value
    assert "builtin" in value
    assert "fn(" in value


def test_hover_unknown_name():
    source = "xyz(1);\n"
    assert hover_at("file:///tmp/h.echo", source, 0, 0) is None


def test_lsp_initialize_and_diagnostics_roundtrip():
    uri = "file:///tmp/demo.echo"
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
                    "text": "say(missing);\n",
                }
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": 0, "character": 0},
            },
        },
        {"jsonrpc": "2.0", "id": 3, "method": "shutdown", "params": None},
        {"jsonrpc": "2.0", "method": "exit"},
    ]
    outbound = exchange(messages)
    init = next(m for m in outbound if m.get("id") == 1)
    assert init["result"]["capabilities"]["hoverProvider"] is True
    assert init["result"]["capabilities"]["textDocumentSync"]["change"] == 1
    published = next(m for m in outbound if m.get("method") == "textDocument/publishDiagnostics")
    assert published["params"]["uri"] == uri
    assert len(published["params"]["diagnostics"]) >= 1
    hover = next(m for m in outbound if m.get("id") == 2)
    assert hover["result"] is not None
    assert "say" in hover["result"]["contents"]["value"]
