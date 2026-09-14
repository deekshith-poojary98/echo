from __future__ import annotations

import json
import re
from pathlib import Path

from echo.frontend.tokens import KEYWORDS, TYPE_NAMES
from echo.runtime.builtins import builtin_names

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GRAMMAR_PATH = PACKAGE_ROOT / "syntaxes" / "echo.tmLanguage.json"
PLAYGROUND_PARSER_PATH = PACKAGE_ROOT.parent / "docs" / ".vitepress" / "theme" / "echoLanguage.ts"

# Reserved builtin names that may land after the current interpreter.
RESERVED_BUILTINS: frozenset[str] = frozenset()


def _load_grammar() -> dict:
    return json.loads(GRAMMAR_PATH.read_text(encoding="utf-8"))


def _collect_strings(node: object) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for value in node.values():
            found.extend(_collect_strings(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_collect_strings(item))
    elif isinstance(node, str):
        found.append(node)
    return found


def _alternation_names(*patterns: str) -> set[str]:
    names: set[str] = set()
    for pattern in patterns:
        for group in re.findall(r"\\b\(([^)]+)\)", pattern):
            names.update(part for part in group.split("|") if part.isidentifier())
        names.update(re.findall(r"\\b([A-Za-z_][A-Za-z0-9_]*)\\b", pattern))
    return names


def test_grammar_json_is_valid() -> None:
    grammar = _load_grammar()
    assert grammar["scopeName"] == "source.echo"
    assert grammar["repository"]["builtins"]["name"] == "support.function.builtin.echo"


def test_keywords_and_types_match_the_language() -> None:
    grammar = _load_grammar()
    repo = grammar["repository"]
    keyword_names = _alternation_names(*_collect_strings(repo["keywords"]), *_collect_strings(repo["function-definitions"]), *_collect_strings(repo["type-definitions"]))

    language_keywords = set(KEYWORDS) - {"true", "false", "null"}
    missing = language_keywords - keyword_names
    assert not missing, f"grammar is missing keywords: {sorted(missing)}"

    type_names = _alternation_names(*_collect_strings(repo["types"]))
    assert type_names == set(TYPE_NAMES)

    literal_names = _alternation_names(*_collect_strings(repo["literals"]))
    assert literal_names == {"true", "false", "null"}


def test_builtin_calls_cover_runtime() -> None:
    grammar = _load_grammar()
    builtin_pattern = grammar["repository"]["builtins"]["match"]
    assert builtin_pattern.startswith(r"\b(")
    assert builtin_pattern.endswith(r")\b")

    listed = _alternation_names(builtin_pattern)
    expected = set(builtin_names()) | RESERVED_BUILTINS
    missing = expected - listed
    extra = listed - expected
    assert not missing, f"grammar is missing builtins: {sorted(missing)}"
    assert not extra, f"grammar has unknown builtins: {sorted(extra)}"


def _ts_string_set(source: str, name: str) -> set[str]:
    match = re.search(rf"const {name} = new Set\(\[(.*?)\]\)", source, re.S)
    assert match, f"missing {name} set in playground parser"
    return set(re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", match.group(1)))


def test_playground_parser_matches_runtime() -> None:
    source = PLAYGROUND_PARSER_PATH.read_text(encoding="utf-8")
    listed = _ts_string_set(source, "BUILTINS")
    expected = set(builtin_names()) | RESERVED_BUILTINS
    missing = expected - listed
    extra = listed - expected
    assert not missing, f"playground parser is missing builtins: {sorted(missing)}"
    assert not extra, f"playground parser has unknown builtins: {sorted(extra)}"

    keywords = _ts_string_set(source, "KEYWORDS")
    language_keywords = set(KEYWORDS) - {"true", "false", "null"}
    assert keywords == language_keywords
    assert _ts_string_set(source, "TYPES") == set(TYPE_NAMES)
    assert r"\.\.\." in source
    assert "->" in source
    assert r"[()[\]{},.:;]" in source


def test_lexer_surface_is_present() -> None:
    grammar = _load_grammar()
    repo = grammar["repository"]
    comments = "\n".join(_collect_strings(repo["comments"]))
    strings = "\n".join(_collect_strings(repo["strings"]))
    interpolation = repo["interpolation"]["begin"]
    numbers = repo["numbers"]["match"]

    assert interpolation == r"\$\{"
    assert "//" in comments
    assert r"/\*" in comments
    assert r'"""' in strings or '"""' in strings
    assert "'''" in strings
    assert r"\.[0-9]+" in numbers
    assert "[eE]" in numbers
    blob = "\n".join(_collect_strings(repo["numbers"]))
    assert "0x" not in blob
    assert "0b" not in blob
