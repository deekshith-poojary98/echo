# Echo Syntax Highlighter

TextMate grammar plus **editor tasks** for **Echo** (`.echo` files) in VS Code and Cursor. The docs site also imports this grammar for Echo code fences (Shiki).

This is **not a language server**. There are no completions, jump-to-definition, or hover docs. Diagnostics in the Problems panel come from running the Echo CLI (`echolang check` / `lint` / `test`) through tasks and problem matchers.

It tracks Echo **v0.7.2**.

## Install

The extension is not published to the Marketplace yet. Install it from this repo.

The Echo CLI must be on `PATH` as **`echolang`** (recommended). Most shells already have an `echo` builtin, so tasks default to `echolang`. After `pipx install` / `pip install`, confirm:

```bash
echolang --version
```

If your executable is named something else, set **`echo.path`** in VS Code/Cursor settings.

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

From this folder in VS Code or Cursor, press **F5**. A new window loads the grammar and tasks. Open `examples/highlight-sample.echo` to check scopes.

## Check / Lint / Format / Test from the editor

Tasks pass **`--plain`** so problem matchers see stable text (not Rich panels).

| Action | How |
| --- | --- |
| Check the current file | Command Palette → **Echo: Check file**, or Terminal → Run Task → **Echo: Check file** |
| Check the workspace | **Echo: Check workspace** (command) or Run Task → **Echo: Check workspace** (`*.echo` recursively, same as `echolang check .`) |
| Lint the workspace | **Echo: Lint** (command) or Run Task → **Echo: Lint workspace** |
| Format the workspace | **Echo: Format** (command) or Run Task → **Echo: Format workspace**. Format Document (`Shift+Alt+F`) also shells out to `echolang fmt` on a temp copy of the buffer |
| Run tests | **Echo: Test** (command) or Run Task → **Echo: Test workspace** (`*_test.echo` discovery, same as the CLI) |

File-scoped variants are also on the task list: **Echo: Check file**, **Echo: Lint file**, **Echo: Format file**, **Echo: Test file**.

Findings land in the **Problems** panel:

- `$echo` — `echo check` / parse errors (`Error[E####]` or `Error:` plus `--> file:line:col`)
- `$echo-lint` — `echo lint` lines `path:line:col: rule: message`
- `$echo-test` / `$echo-test-detail` — `echo test` failures that include a `--> file:line:col` location

`FAIL path::testName` summary lines without a column are not matched. Install the CLI; the extension does not embed the interpreter.

To copy tasks into a workspace instead of using the provider, see `templates/tasks.json`.

## What it highlights

| Category | Examples |
| --- | --- |
| Keywords | `fn`, `if`, `else`, `while`, `for`, `foreach`, `return`, `break`, `continue`, `in`, `by`, `use`, `mut`, `watch`, `const`, `type`, `import`, `export`, `from` |
| Types | `int`, `float`, `str`, `bool`, `list`, `hash`, `dynamic`, `void` |
| Literals | `true`, `false`, `null` |
| Builtins | Distinct from user functions: `say`, `assert`, `expect` / `expectEq` / `expectNeq`, `fail`, `*Or` twins, host/stdlib names from 0.4–0.5.x |
| Comments | `//` line and `/* */` block |
| Strings | `"..."`, `'...'`, `"""..."""`, `'''...'''`, escapes, and `${...}` interpolation (nested hashes inside `${}` keep matching braces) |
| Numbers | Integers, `.5`, `1.5`, `1e3`, `1e-3`. Echo has no hex (`0x`) or binary (`0b`) literals |
| Operators | Arithmetic, comparison, `&&` `||` `!`, `..` `...`, `+=` and friends, `->` `=>` |
| Names | `fn` definitions, user calls, and `TYPE`-style constants |

Snippets cover `fn testName()`, `expect` / `expectEq`, and `fail`.

The grammar does **not** invent syntax Echo does not have (`try`/`catch`, classes, `as` as a keyword, hex/binary literals).

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

The playground editor uses a separate CodeMirror stream parser (`docs/.vitepress/theme/echoLanguage.ts`), not this TextMate file. Keep its `BUILTINS` set in the same alphabetical order as this grammar.

## License

MIT, same as Echo.
