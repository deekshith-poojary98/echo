# CLI and Execution Model

## Overview
Echo source files are tokenized, parsed, and interpreted at runtime.

## Syntax
```bash
python src/main.py file.echo
python src/main.py file.echo --plain
```

## How Echo Runs
1. Lexer reads the source file and produces tokens
2. Parser turns tokens into an AST
3. Interpreter executes the AST directly

## CLI
### Run a file
```bash
python src/main.py program.echo
```

### Plain output mode
```bash
python src/main.py program.echo --plain
```

Use plain mode when you want simple text output without Rich panels.

### Analyze without running
```bash
echo check program.echo
echo check src/
echo check program.echo --plain
```

`check` lexes, parses, and analyzes each file and its import graph. It does not execute. A directory argument checks `*.echo` files recursively. Explicit file paths always check. Success prints nothing and exits 0. If any file fails, each diagnostic is printed and the process exits 1 after every path has been analyzed (it does not stop at the first bad file). Missing path exits 1. `echo check` with no path prints help and exits 2. The first argument must be the word `check`; `echo check.echo` still runs a file named `check.echo`. `--plain` disables Rich panels. The VS Code / Cursor extension can run **Echo: Check file** or **Echo: Check workspace** (`--plain`) and match diagnostics into the Problems panel.

### REPL
```bash
echo
echo --plain
```

With no source file, Echo starts a REPL. `--plain` uses the same plain diagnostics as file runs.

One process is one session: variables, functions, and type aliases persist across `echo>` submissions, and builtins remain available. `use mut` in a later `fn` can assign a variable declared earlier in the session, the same way a file can.

A submission can span lines: Echo keeps reading while `{` is unclosed, or while a triple-quoted string is unterminated, and shows `... ` until the input is complete. A one-line `if true { say(1); }` works.

`import name from "module";` resolves sibling `.echo` files from the current working directory, loads them with the existing module loader, and merges the imported bindings into the session. The loaded module is not re-initialized if you import from it again.

Empty lines at a fresh `echo> ` prompt are ignored. A syntax, semantic, or runtime error prints an Echo diagnostic and returns to the prompt; it does not kill the process, print a Python traceback, or drop bindings from earlier successful submissions. If analysis fails, the snippet is not executed. A runtime error does not roll back the interpreter, so a failed `x: int = 1; bad();` may still leave `x` assigned.

Quit with `exit(code)` (the process returns that code) or EOF (Ctrl-D), which exits 0. Session state does not survive process exit. Ctrl-C cancels the current submission and returns to `echo> `.

### Run tests
```bash
echo test program.echo
echo test path/foo_test.echo
echo test tests/
echo test program.echo --plain
```

Runs Echo tests. A directory argument recursively runs `*_test.echo` files. An explicit file path always runs, even if it is not named `*_test.echo`. `echo test` with no path prints help and exits 2.

Each discovered file is a test file. If it defines top-level zero-argument `fn testXxx()` functions, the runner calls each as a separate unit after running the remaining top-level statements once as setup. If there are no such functions, the file itself is one unit.

`expect(cond, message)`, `expectEq(left, right, message)`, and `expectNeq(left, right, message)` record a failure and continue under this runner (codes E2826 / E2827 / E2828). Outside `echo test` they abort like `assert`. `assert` / `fail` still abort the current unit; later units still run. Parse and load errors fail that file as a unit.

The process exits 0 if every unit passed and 1 if any failed. `exit(0)` in a unit passes that unit; any other `exit(n)` fails it. The runner exit code is 0 or 1 (or 2 for usage), not the program's `exit(n)`.

Output is a line per unit then a count:

```text
ok   path/foo_test.echo::testAdd
FAIL path/foo_test.echo::testSub
     Error[E2827]: sub
     expected 3, got 4
2 passed, 1 failed
```

Program `say` output is shown. There is no `test "name" { }` syntax. The first argument must be the word `test`; `echo test.echo` still runs a file named `test.echo`. The editor extension can run `echo test --plain` as a task and match location-bearing failures.

### Format source files
```bash
echo fmt program.echo
echo fmt src/
echo fmt program.echo --check
echo fmt program.echo --plain
```

Rewrites Echo sources in place to the canonical layout (4-space indent, comments kept, `else if` flattening, parentheses from operator precedence). A directory argument formats `*.echo` files recursively. `--check` prints each path that would change and exits 1; already-formatted files print nothing and exit 0. Parse errors use the same diagnostics as `echo check` and do not write the file. `echo fmt` with no path prints help and exits 2. The first argument must be the word `fmt`; `echo fmt.echo` still runs a file named `fmt.echo`. The editor extension can run this command (Format Document / Format workspace).

Number literals may be respelled (`1e3` → `1000.0`). Strings are wrapped from raw lexemes and are not re-escaped, so quote style may change (`'hello'` → `"hello"`).

### Lint source files
```bash
echo lint program.echo
echo lint src/
echo lint program.echo --plain
```

Reports style and convention findings without running the program. A directory argument lints `*.echo` files recursively. Each finding prints `path:line:col: rule: message`. Any finding exits 1; a clean tree prints nothing and exits 0. Parse errors use the same diagnostics as `echo check`. `echo lint` with no path prints help and exits 2. The first argument must be the word `lint`; `echo lint.echo` still runs a file named `lint.echo`. The editor extension can run this command as a task (`--plain`) and match findings into the Problems panel.

Rules:

| Rule | What it flags |
| --- | --- |
| `unused-local` | declared local, parameter, or loop variable that is never read |
| `unused-function` | function never called in this file, not exported, and not a zero-arg `test*` entry |
| `unused-import` | imported name that is never used |
| `comparison-to-bool` | `== true` / `!= false` and the other boolean-literal comparisons |
| `redundant-by-one` | explicit `by 1` on `for` (the formatter omits it) |
| `empty-block` | empty `if` / `else` body or empty function body |
| `shadow-builtin` | a declared name that shadows a builtin |
| `test-naming` | top-level `fn` that looks like a test but is not a zero-arg `testXxx` unit |
| `self-assign` | `x = x` or `x = x + 0` / `x = 0 + x` |
| `unreachable-after-fail` | a later statement in the same block after `fail(...)` or `return` |

This is not a second typechecker. Semantic errors stay `echo check`. Unused parameters are `unused-local`. `unused-export` and `redundant-parens` are not rules: exports are for other files, and grouping parentheses are not kept on the AST.

## Notes
- The file passed to the CLI is the entry module when it contains `import`.
- Errors are reported by category: syntax, semantic, name, type, argument, index, mutation, or execution.

## See Also
- [Quick Start](/getting-started/quick-start)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
- [Known Limitations](/errors-diagnostics/known-limitations)
