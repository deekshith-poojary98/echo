#!/usr/bin/env python3
"""Sync builtin + std inventories from runtime into docs and highlighters.

Source of truth:
  - ``echo.runtime.builtins.builtin_names()``
  - install-tree ``echo.std`` modules (``std_root()``)

Writes:
  - docs/reference/builtin-inventory.md
  - docs/reference/std-inventory.md
  - echo-syntax-highlighter/syntaxes/echo.tmLanguage.json (builtins match)
  - docs/.vitepress/theme/echoLanguage.ts (BUILTINS set)

Usage:
  python tools/sync_builtins.py          # write
  python tools/sync_builtins.py --check  # exit 1 if drift
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from echo.runtime.builtins import builtin_names  # noqa: E402
from echo.std import list_std_inventory, std_root  # noqa: E402

INVENTORY_PATH = REPO_ROOT / "docs" / "reference" / "builtin-inventory.md"
STD_INVENTORY_PATH = REPO_ROOT / "docs" / "reference" / "std-inventory.md"
GRAMMAR_PATH = REPO_ROOT / "echo-syntax-highlighter" / "syntaxes" / "echo.tmLanguage.json"
PLAYGROUND_PARSER_PATH = REPO_ROOT / "docs" / ".vitepress" / "theme" / "echoLanguage.ts"

INVENTORY_HEADER = """\
---
title: Builtin Inventory
description: Auto-generated list of Echo prelude builtins
---

# Builtin Inventory

Auto-generated from `builtin_names()` by `tools/sync_builtins.py`.
Do not edit by hand — run `python tools/sync_builtins.py` after adding a builtin.

Narrative docs stay in [Built-in Methods](/standard-library/built-in-methods).
Install-tree modules: [Std Inventory](/reference/std-inventory).

"""

STD_INVENTORY_HEADER = """\
---
title: Std Inventory
description: Auto-generated list of Echo install-tree std/… modules
---

# Std Inventory

Auto-generated from the install-tree `std/` modules by `tools/sync_builtins.py`.
Do not edit by hand — run `python tools/sync_builtins.py` after adding a std module.

CLI: `elang std` / `elang std --exports`. Module semantics: [Modules](/module-semantics).
Prelude builtins: [Builtin Inventory](/reference/builtin-inventory).

"""


def sorted_names() -> list[str]:
    return sorted(builtin_names())


def render_inventory(names: list[str]) -> str:
    lines = [INVENTORY_HEADER, f"**Count:** {len(names)}", "", "| Name |", "| --- |"]
    for name in names:
        lines.append(f"| `{name}` |")
    lines.append("")
    return "\n".join(lines)


def render_std_inventory() -> str:
    rows = list_std_inventory(std_root())
    lines = [
        STD_INVENTORY_HEADER,
        f"**Modules:** {len(rows)}",
        "",
        "| Module | Exports |",
        "| --- | --- |",
    ]
    for specifier, _path, exports in rows:
        export_cell = ", ".join(f"`{name}`" for name in exports) if exports else "—"
        lines.append(f"| `{specifier}` | {export_cell} |")
    lines.append("")
    return "\n".join(lines)


def render_grammar_match(names: list[str]) -> str:
    return r"\b(" + "|".join(names) + r")\b"


def render_ts_builtins(names: list[str]) -> str:
    body = ",\n".join(f"  '{name}'" for name in names)
    return (
        "// Keep in sync with BUILTIN_NAMES in src/echo/runtime/builtins.py\n"
        "// (and echo-syntax-highlighter/syntaxes/echo.tmLanguage.json).\n"
        "// Prefer: python tools/sync_builtins.py\n"
        "const BUILTINS = new Set([\n"
        f"{body},\n"
        "])"
    )


def update_grammar(names: list[str], *, write: bool) -> bool:
    grammar = json.loads(GRAMMAR_PATH.read_text(encoding="utf-8"))
    current = grammar["repository"]["builtins"]["match"]
    expected = render_grammar_match(names)
    if current == expected:
        return False
    if write:
        grammar["repository"]["builtins"]["match"] = expected
        GRAMMAR_PATH.write_text(json.dumps(grammar, indent=2) + "\n", encoding="utf-8")
    return True


def update_playground_parser(names: list[str], *, write: bool) -> bool:
    source = PLAYGROUND_PARSER_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r"// Keep in sync with BUILTIN_NAMES.*?\nconst BUILTINS = new Set\(\[.*?\]\)",
        re.S,
    )
    expected_block = render_ts_builtins(names)
    match = pattern.search(source)
    if match is None:
        raise RuntimeError(f"BUILTINS set not found in {PLAYGROUND_PARSER_PATH}")
    if match.group(0) == expected_block:
        return False
    if write:
        PLAYGROUND_PARSER_PATH.write_text(pattern.sub(expected_block, source, count=1), encoding="utf-8")
    return True


def update_inventory(names: list[str], *, write: bool) -> bool:
    expected = render_inventory(names)
    current = INVENTORY_PATH.read_text(encoding="utf-8") if INVENTORY_PATH.is_file() else ""
    if current == expected:
        return False
    if write:
        INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        INVENTORY_PATH.write_text(expected, encoding="utf-8")
    return True


def update_std_inventory(*, write: bool) -> bool:
    expected = render_std_inventory()
    current = STD_INVENTORY_PATH.read_text(encoding="utf-8") if STD_INVENTORY_PATH.is_file() else ""
    if current == expected:
        return False
    if write:
        STD_INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        STD_INVENTORY_PATH.write_text(expected, encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without writing; exit 1 if anything is out of date",
    )
    args = parser.parse_args(argv)
    names = sorted_names()
    write = not args.check
    std_count = len(list_std_inventory(std_root()))
    changed = [
        ("inventory", update_inventory(names, write=write)),
        ("std inventory", update_std_inventory(write=write)),
        ("grammar", update_grammar(names, write=write)),
        ("playground parser", update_playground_parser(names, write=write)),
    ]
    drifted = [label for label, did in changed if did]
    if args.check:
        if drifted:
            print("builtin sync drift:", ", ".join(drifted))
            print("run: python tools/sync_builtins.py")
            return 1
        print(f"builtin sync ok ({len(names)} builtins, {std_count} std modules)")
        return 0
    if drifted:
        print("updated:", ", ".join(drifted))
    else:
        print(f"already in sync ({len(names)} builtins, {std_count} std modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
