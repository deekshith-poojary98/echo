from __future__ import annotations

import re
from pathlib import Path

from echo.errors import ModuleResolveError

_SEGMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DRIVE = re.compile(r"^[A-Za-z]:")


class ModuleResolver:
    def resolve(self, importer_path: str | Path, module_name: str) -> Path:
        parts = self._parse_specifier(module_name)
        importer = Path(importer_path).expanduser()
        candidate = importer.parent.joinpath(*parts).with_suffix(".echo")
        if not candidate.is_file():
            looked = self._looked_for_label(importer, candidate)
            raise ModuleResolveError(
                f"module '{module_name}' not found",
                code="E3002",
                help_text=f"looked for {looked}",
            )
        return self.canonicalize(candidate)

    def validate_module_name(self, module_name: str) -> None:
        self._parse_specifier(module_name)

    def _parse_specifier(self, module_name: str) -> list[str]:
        if not isinstance(module_name, str) or not module_name:
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
                help_text="specifier must be a non-empty module path",
            )
        if "\\" in module_name:
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
                help_text="use '/' separators; backslashes are not allowed",
            )
        if module_name.startswith("/") or _DRIVE.match(module_name):
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
                help_text="use a path relative to the importing file",
            )
        if "//" in module_name or module_name.endswith("/"):
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
                help_text="specifier must name a module file, not a directory",
            )
        if module_name.endswith(".echo"):
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
                help_text="omit the .echo suffix; Echo adds it",
            )

        parts = module_name.split("/")
        index = 0
        while index < len(parts) and parts[index] in {".", ".."}:
            index += 1
        if index == len(parts):
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
                help_text="specifier must end with a module name",
            )
        for part in parts[index:]:
            if part in {".", ".."}:
                raise ModuleResolveError(
                    f"invalid module specifier '{module_name}'",
                    code="E3001",
                    help_text="'..' is only allowed at the start of a specifier",
                )
            if not _SEGMENT.fullmatch(part):
                raise ModuleResolveError(
                    f"invalid module specifier '{module_name}'",
                    code="E3001",
                    help_text="use a bare name, ./path, ../path, or nested/segments",
                )
        return parts

    def _looked_for_label(self, importer: Path, candidate: Path) -> str:
        try:
            return candidate.relative_to(importer.parent).as_posix()
        except ValueError:
            return candidate.as_posix()

    def canonicalize(self, path: str | Path) -> Path:
        return Path(path).expanduser().resolve()
