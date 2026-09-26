from pathlib import Path
import subprocess
import sys

from echo.std import list_std_modules, std_root

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC = REPO_ROOT / "tools" / "sync_builtins.py"
STD_INVENTORY = REPO_ROOT / "docs" / "reference" / "std-inventory.md"


def test_sync_rewrites_missing_std_inventory():
    # Ensure --check fails if the generated page is deleted, then rewrite restores it.
    backup = STD_INVENTORY.read_text(encoding="utf-8")
    STD_INVENTORY.unlink()
    try:
        result = subprocess.run(
            [sys.executable, str(SYNC), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "std inventory" in result.stdout
        write = subprocess.run(
            [sys.executable, str(SYNC)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert write.returncode == 0
        assert STD_INVENTORY.is_file()
        text = STD_INVENTORY.read_text(encoding="utf-8")
        for specifier in list_std_modules(std_root()):
            assert f"`{specifier}`" in text
    finally:
        STD_INVENTORY.write_text(backup, encoding="utf-8")
