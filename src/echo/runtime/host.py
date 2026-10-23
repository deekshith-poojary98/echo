from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Host:
    """Process host for Echo programs. Not language syntax."""

    args: list[str] = field(default_factory=list)
    environ: dict[str, str] | None = None
    allow_files: bool = True
    allow_run: bool = True
    allow_http: bool = True
    require_std: bool = False
    cwd: Path | None = None
    http_timeout: float = 30.0

    def program_args(self) -> list[str]:
        return list(self.args)

    def environment(self) -> dict[str, str]:
        if self.environ is not None:
            return self.environ
        return dict(os.environ)

    def resolve_path(self, path: str, *, follow_symlinks: bool = True) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        root = self.cwd if self.cwd is not None else Path.cwd()
        base = root / candidate
        try:
            if follow_symlinks:
                return base.resolve()
            # Resolve parents (and detect symlink cycles there) but keep the
            # final name so delete ops remove the named entry, not its target.
            return base.parent.resolve() / base.name
        except RuntimeError as exc:
            # pathlib.resolve() raises RuntimeError on symlink cycles (ELOOP),
            # not OSError. Host callers already map OSError to Echo errors.
            raise OSError(str(exc)) from exc

    def working_directory(self) -> Path:
        root = self.cwd if self.cwd is not None else Path.cwd()
        return root.resolve()

    def file_exists(self, path: str) -> bool:
        return self.resolve_path(path).is_file()

    def is_dir(self, path: str) -> bool:
        return self.resolve_path(path).is_dir()

    def list_entries(self, path: str) -> list[str]:
        names = [entry.name for entry in self.resolve_path(path).iterdir()]
        names.sort()
        return names

    def mkdir(self, path: str) -> None:
        self.resolve_path(path).mkdir()

    def mkdir_all(self, path: str) -> None:
        target = self.resolve_path(path)
        if target.is_file():
            raise FileExistsError(path)
        target.mkdir(parents=True, exist_ok=True)

    def remove_file(self, path: str) -> None:
        target = self.resolve_path(path, follow_symlinks=False)
        # is_dir() follows the final symlink. A symlink to a directory is still
        # a removable directory *entry*, like Unix rm — following first used
        # to delete the target file/tree and leave a dangling link.
        if target.is_dir() and not target.is_symlink():
            raise IsADirectoryError(path)
        target.unlink()

    def remove_tree(self, path: str) -> None:
        target = self.resolve_path(path, follow_symlinks=False)
        if target.is_symlink() or target.is_file():
            target.unlink()
            return
        if not target.exists():
            raise FileNotFoundError(path)
        if target.is_dir():
            shutil.rmtree(target)
            return
        target.unlink()

    def copy_file(self, src: str, dest: str) -> None:
        source = self.resolve_path(src)
        target = self.resolve_path(dest)
        if source.is_dir():
            raise IsADirectoryError(src)
        if target.is_dir():
            raise IsADirectoryError(dest)
        shutil.copyfile(source, target)

    def run_process(self, command: str, args: list[str]) -> dict[str, object]:
        if not self.allow_run:
            raise PermissionError("run is not available in this host")
        completed = subprocess.run(
            [command, *args],
            cwd=self.working_directory(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
        )
        return {
            "code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    def http_get(self, url: str, headers: dict[str, str] | None = None) -> dict[str, object]:
        if not self.allow_http:
            raise PermissionError("http is not available in this host")
        from echo.core.httputil import http_get

        return http_get(url, headers, timeout=self.http_timeout)

    def http_post(self, url: str, body: str, headers: dict[str, str] | None = None) -> dict[str, object]:
        if not self.allow_http:
            raise PermissionError("http is not available in this host")
        from echo.core.httputil import http_post

        return http_post(url, body, headers, timeout=self.http_timeout)
