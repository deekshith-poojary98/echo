from __future__ import annotations

import os
import re
from pathlib import Path

from echo.errors import ModuleResolveError
from echo.std import std_root as default_std_root

_SEGMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DRIVE = re.compile(r"^[A-Za-z]:")


class ModuleResolver:
    def __init__(self, std_root: str | Path | None = None) -> None:
        if std_root is not None:
            root = Path(std_root)
        else:
            env = os.environ.get("ECHO_STD_ROOT")
            root = Path(env) if env else default_std_root()
        self.std_root = root.expanduser().resolve()

    def resolve(self, importer_path: str | Path, module_name: str) -> Path:
        parts = self._parse_specifier(module_name)
        if parts[0] == "std":
            return self._resolve_std(module_name, parts)
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

    def _resolve_std(self, module_name: str, parts: list[str]) -> Path:
        if len(parts) < 2:
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
                help_text="use std/module (for example std/meta)",
            )
        candidate = self.std_root.joinpath(*parts[1:]).with_suffix(".echo")
        if not candidate.is_file():
            try:
                looked = candidate.relative_to(self.std_root).as_posix()
            except ValueError:
                looked = candidate.as_posix()
            raise ModuleResolveError(
                f"module '{module_name}' not found",
                code="E3002",
                help_text=f"looked for {looked} under Echo std ({self.std_root})",
            )
        return self.canonicalize(candidate)

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
                help_text="use a path relative to the importing file, or std/…",
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
                    help_text="use a bare name, ./path, ../path, nested/segments, or std/…",
                )
        if parts == ["std"]:
            raise ModuleResolveError(
                f"invalid module specifier '{module_name}'",
                code="E3001",
                help_text="use std/module (for example std/meta)",
            )
        return parts

    def _looked_for_label(self, importer: Path, candidate: Path) -> str:
        try:
            return candidate.relative_to(importer.parent).as_posix()
        except ValueError:
            return candidate.as_posix()

    def canonicalize(self, path: str | Path) -> Path:
        return Path(path).expanduser().resolve()
