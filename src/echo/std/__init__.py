"""Echo install-tree standard modules (`import … from "std/…"`)."""

from __future__ import annotations

from pathlib import Path


def std_root() -> Path:
    """Directory that backs the reserved `std/…` import prefix."""
    return Path(__file__).resolve().parent
