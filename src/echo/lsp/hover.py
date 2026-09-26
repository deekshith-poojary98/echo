from __future__ import annotations

from echo.frontend.lexer import Lexer
from echo.frontend.tokens import TokenType
from echo.lsp.protocol import lsp_to_echo_position
from echo.runtime.builtin_types import builtin_fn_type
from echo.runtime.builtins import BUILTIN_PARAMS, STANDALONE_PARAMS, builtin_names
from echo.runtime.values import format_type


def identifier_at(text: str, line: int, column: int, *, filename: str) -> str | None:
    try:
        tokens = Lexer().tokenize(text, filename=filename)
    except Exception:  # noqa: BLE001 — hover / definition are best-effort
        return None
    for token in tokens:
        if token.type != TokenType.IDENTIFIER or token.line != line:
            continue
        start = token.column
        end = start + len(token.lexeme)
        # Inclusive end so the cursor after the last character still hits.
        if start <= column <= end:
            return token.lexeme
    return None


def hover_at(uri: str, text: str, line: int, character: int) -> dict | None:
    """Return an LSP Hover result for a builtin at the given 0-based position, or None."""
    echo_line, echo_col = lsp_to_echo_position(line, character)
    name = identifier_at(text, echo_line, echo_col, filename=uri or "<lsp>")
    if name is None or name not in builtin_names():
        return None
    signature = format_type(builtin_fn_type(name))
    params = STANDALONE_PARAMS.get(name) or BUILTIN_PARAMS.get(name) or []
    lines = [f"```echo\n{name}: {signature}\n```", "", f"**builtin** `{name}`"]
    if params:
        lines.append("")
        lines.append("Parameters: " + ", ".join(f"`{p}`" for p in params))
    return {
        "contents": {
            "kind": "markdown",
            "value": "\n".join(lines),
        }
    }
