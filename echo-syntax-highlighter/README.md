# Echo Syntax Highlighter

TextMate grammar for **Echo** (`.echo` files). It is the highlighting used in VS Code / Cursor and, via import, in the Echo docs site (Shiki code fences).

This package is **highlight-only**. There is no language server, completions, or diagnostics (LSP is held).

It tracks Echo **v0.5.6**.

## Install

The extension is not published to the Marketplace yet. Install it from this repo.

### VS Code

Symlink or copy this folder into your extensions directory, then reload the window:

```bash
# macOS / Linux
ln -s "$(pwd)/echo-syntax-highlighter" ~/.vscode/extensions/echo-syntax-highlighter

# Windows (Command Prompt, from the repo root)
mklink /D "%USERPROFILE%\.vscode\extensions\echo-syntax-highlighter" "%CD%\echo-syntax-highlighter"
```

### Cursor

Same layout, different extensions folder:

```bash
ln -s "$(pwd)/echo-syntax-highlighter" ~/.cursor/extensions/echo-syntax-highlighter
```

Open any `.echo` file. The status bar language mode should read **Echo**.

### Develop against a host window

From this folder in VS Code or Cursor, press **F5**. A new window loads the grammar. Open `examples/highlight-sample.echo` to check scopes.

## What it highlights

| Category | Examples |
| --- | --- |
| Keywords | `fn`, `if`, `else`, `while`, `for`, `foreach`, `return`, `break`, `continue`, `in`, `by`, `use`, `mut`, `watch`, `type`, `import`, `export`, `from` |
| Types | `int`, `float`, `str`, `bool`, `list`, `hash`, `dynamic`, `void` |
| Literals | `true`, `false`, `null` |
| Builtins | Distinct from user functions: `say`, `assert`, `expect` / `expectEq` / `expectNeq`, `fail`, `*Or` twins, host/stdlib names from 0.4–0.5.x |
| Comments | `//` line and `/* */` block |
| Strings | `"..."`, `'...'`, `"""..."""`, `'''...'''`, escapes, and `${...}` interpolation (nested hashes inside `${}` keep matching braces) |
| Numbers | Integers, `.5`, `1.5`, `1e3`, `1e-3`. Echo has no hex (`0x`) or binary (`0b`) literals |
| Operators | Arithmetic, comparison, `&&` `||` `!`, `..` `...`, `+=` and friends, `->` `=>` |
| Names | `fn` definitions, user calls, and `TYPE`-style constants |

The grammar does **not** invent syntax Echo does not have (`try`/`catch`, classes, slice syntax, `as` as a keyword, hex/binary literals).

## Keep the builtin list in sync

Builtin names are a **manual** list in `syntaxes/echo.tmLanguage.json`, under the `builtins` repository pattern (`support.function.builtin.echo`).

When Echo gains or renames a builtin:

1. Read `BUILTIN_NAMES` in `src/echo/runtime/builtins.py`.
2. Add any reserved names that are not in that set yet.
3. Put the names in the `builtins` `match` regex, **alphabetically**, each followed by `\\s*(?=\\()` so only calls highlight as builtins.
4. Run the sync test:

```bash
python -m pytest echo-syntax-highlighter/tests/test_grammar_sync.py -q
```

Keywords and type names come from `src/echo/frontend/tokens.py` (`KEYWORDS`, `TYPE_NAMES`). Number, string, comment, and interpolation rules must match `src/echo/frontend/lexer.py`.

The docs site imports this grammar directly (`docs/.vitepress/config.ts`). Updating the JSON updates markdown Echo fences; you do not copy the file into `docs/`.

The playground editor uses a separate CodeMirror stream parser (`docs/.vitepress/theme/echoLanguage.ts`), not this TextMate file.

## License

MIT, same as Echo.
