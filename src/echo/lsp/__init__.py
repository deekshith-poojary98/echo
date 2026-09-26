"""Thin Echo language server stub (2.1.2).

Stdio JSON-RPC: analyzer diagnostics + builtin hover.
Not a full IDE language server product.
"""

from echo.lsp.server import run_stdio

__all__ = ["run_stdio"]
