"""Echo desktop IDE (IDLE-style Tk window)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["launch"]


def launch(source_path: str | Path | None = None) -> int:
    """Open the Echo IDE window. Blocks until the window is closed."""
    from echo.ide.app import launch as _launch

    return _launch(source_path)
