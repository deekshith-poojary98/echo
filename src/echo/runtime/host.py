from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Host:
    """Process host for Echo programs. Not language syntax."""

    args: list[str] = field(default_factory=list)
    environ: dict[str, str] | None = None
    allow_files: bool = True
    cwd: Path | None = None

    def program_args(self) -> list[str]:
        return list(self.args)

    def environment(self) -> dict[str, str]:
        if self.environ is not None:
            return self.environ
        return dict(os.environ)

    def resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        root = self.cwd if self.cwd is not None else Path.cwd()
        return (root / candidate).resolve()
