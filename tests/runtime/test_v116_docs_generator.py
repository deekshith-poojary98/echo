from pathlib import Path
import subprocess
import sys

from echo.runtime.builtins import builtin_names
from echo.std import list_std_inventory, list_std_modules, std_root

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC = REPO_ROOT / "tools" / "sync_builtins.py"
INVENTORY = REPO_ROOT / "docs" / "reference" / "builtin-inventory.md"
STD_INVENTORY = REPO_ROOT / "docs" / "reference" / "std-inventory.md"


def test_sync_builtins_check_passes():
    result = subprocess.run(
        [sys.executable, str(SYNC), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "builtin sync ok" in result.stdout
    assert "std modules" in result.stdout


def test_inventory_lists_every_runtime_builtin():
    text = INVENTORY.read_text(encoding="utf-8")
    assert "Auto-generated" in text
    assert f"**Count:** {len(builtin_names())}" in text
    assert "/reference/std-inventory" in text
    for name in sorted(builtin_names()):
        assert f"`{name}`" in text, name


def test_std_inventory_lists_every_install_tree_module():
    text = STD_INVENTORY.read_text(encoding="utf-8")
    assert "Auto-generated" in text
    rows = list_std_inventory(std_root())
    assert f"**Modules:** {len(rows)}" in text
    assert list_std_modules(std_root()) == [spec for spec, _path, _exports in rows]
    for specifier, _path, exports in rows:
        assert f"`{specifier}`" in text, specifier
        for name in exports:
            assert f"`{name}`" in text, f"{specifier}:{name}"


def test_built_in_methods_mentions_every_builtin():
    docs = (REPO_ROOT / "docs" / "standard-library" / "built-in-methods.md").read_text(encoding="utf-8")
    missing = [name for name in sorted(builtin_names()) if name not in docs]
    assert not missing, f"built-in-methods.md missing builtins: {missing}"
