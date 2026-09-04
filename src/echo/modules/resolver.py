from __future__ import annotations

import re
from pathlib import Path

from echo.errors import ModuleResolveError

_BARE_MODULE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ModuleResolver:
    def resolve(self, importer_path: str | Path, module_name: str) -> Path:
        self.validate_module_name(module_name)
        importer = Path(importer_path).expanduser()
        candidate = importer.parent / f"{module_name}.echo"
        if not candidate.is_file():
            raise ModuleResolveError(
                f"module '{module_name}' not found",
                code="E3002",
            )
        return self.canonicalize(candidate)

    def validate_module_name(self, module_name: str) -> None:
        if not isinstance(module_name, str) or not _BARE_MODULE_NAME.fullmatch(module_name):
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
            )

    def canonicalize(self, path: str | Path) -> Path:
        return Path(path).expanduser().resolve()
