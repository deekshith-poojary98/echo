# CLI and Execution Model

Run path: tokenize → parse → analyze → interpret. The CLI wraps that pipeline.

```bash
elang file.echo
elang file.echo --plain
```

## Pipeline

1. Lexer → tokens
2. Parser → AST
3. Analyzer → scopes / types / names
4. Interpreter → run the AST

## CLI

### Run a file

```bash
elang program.echo
```

### Plain output mode

```bash
elang program.echo --plain
```

`--plain` drops Rich panels for simple text diagnostics.

### Analyze without running

```bash
elang check program.echo
elang check src/
elang check program.echo --plain
```

`check` lexes, parses, and analyzes each file and its import graph. It does not execute.

- Directory → recursive `*.echo`. Explicit file paths always check.
- Success: silence, exit 0. Failure: print every diagnostic, exit 1 after all paths (does not stop at the first bad file).
- Missing path → exit 1. No path → help, exit 2.
- First argv token must be the word `check`; `elang check.echo` still runs a file named `check.echo`.
- `--plain` disables Rich panels.
- Editor: **Echo: Check file** / **Echo: Check workspace** (`--plain`) → Problems panel.

### REPL

```bash
elang
elang --plain
```

No source file → REPL. `--plain` uses the same plain diagnostics as file runs.

One process is one session: variables, functions, and type aliases persist across `echo>` submissions. Builtins stay available. `use mut` in a later `fn` can assign a name declared earlier in the session.

Continuation: keeps reading while `{` is unclosed or a triple-quoted string is open; shows `... ` until complete. One-line `if true { say(1); }` works.

`import name from "module";` resolves sibling `.echo` files from the cwd, loads with the module loader, merges bindings into the session. Re-import does not re-initialize the module.

Empty lines at a fresh `echo> ` are ignored. Syntax / semantic / runtime errors print an Echo diagnostic and return to the prompt — no process kill, no Python traceback, no drop of earlier successful bindings. Failed analysis does not execute. A runtime error does not roll back the interpreter (`x: int = 1; bad();` may leave `x`).

Quit: `exit(code)` or EOF (Ctrl-D → exit 0). Session state dies with the process. Ctrl-C cancels the current submission and returns to `echo> `.

### Run tests

```bash
elang test program.echo
elang test path/foo_test.echo
elang test tests/
elang test program.echo --plain
elang test tests/ --run '*Add*'
elang test path/foo_test.echo -run testAdd --plain
elang test tests/ --json
elang test tests/ --run '*Add*' --json --plain
```

Native test runner. No `test "name" { }` syntax.

**Discovery**

- Directory → recursive `*_test.echo`. Explicit file path always runs (even if not `*_test.echo`).
- No path → help, exit 2.
- First argv token must be `test`; `elang test.echo` still runs that file.

**Units**

- Zero-arg top-level `fn testXxx()` → each is a unit (remaining top-level runs once as setup).
- No such functions → the file is one unit.

**`-run` / `--run PATTERN`**

- Keeps `testXxx` **function** units whose names match a case-sensitive glob (`*`, exact names).
- Does not filter file names. Non-matching units are skipped, not failed.
- File with no matching units is skipped (setup does not run) and does not fail.
- Quote globs in the shell (`--run '*Add*'`). Without `-run`, every unit runs.

**`--json`**

- One JSON object on stdout instead of `ok` / `FAIL` lines and the summary.
- Composes with `-run` and `--plain` (JSON has no color).
- Fields: `passed`, `failed`, `skipped`, `units[]` with `name`, `passed` / `skipped`, and on failure `message` + `location` when present.
- Exit codes stay 0 / 1 / 2.

**Assertions**

- `expect` / `expectEq` / `expectNeq` record and continue under this runner (`E2826`–`E2828`). Outside `elang test` they abort like `assert`.
- `assert` / `fail` still abort the current unit; later units still run.
- Parse / load errors fail that file as a unit.

**Exit**

- Process exit 0 if every unit passed, 1 if any failed (2 for usage).
- `exit(0)` in a unit passes it; any other `exit(n)` fails it. Runner exit is not the program's `exit(n)`.

Human report:

```text
ok   path/foo_test.echo::testAdd
FAIL path/foo_test.echo::testSub
     Error[E2827]: sub
     expected 3, got 4
2 passed, 1 failed
```

`--json` sample:

```json
{
  "passed": 2,
  "failed": 1,
  "skipped": 0,
  "units": [
    {"name": "path/foo_test.echo::testAdd", "passed": true},
    {
      "name": "path/foo_test.echo::testSub",
      "passed": false,
      "message": "Error[E2827]: sub",
      "location": "path/foo_test.echo:4:5"
    }
  ]
}
```

Program `say` output is shown. Editor can run `elang test --plain` as a task.

### Format source files

```bash
elang fmt program.echo
elang fmt src/
elang fmt program.echo --check
elang fmt program.echo --plain
```

Rewrites sources in place to the canonical layout (4-space indent, comments kept, `else if` flattening, parentheses from operator precedence).

- Directory → recursive `*.echo`.
- `--check`: print paths that would change, exit 1; clean → silence, exit 0.
- Parse errors match `elang check`; file is not written.
- No path → help, exit 2. First token must be `fmt`; `elang fmt.echo` still runs that file.
- Editor: Format Document / Format workspace.

Side effects of formatting: number literals may respell (`1e3` → `1000.0`). Strings wrap from raw lexemes and are not re-escaped, so quote style may change (`'hello'` → `"hello"`).

### Lint source files

```bash
elang lint program.echo
elang lint src/
elang lint program.echo --plain
```

Style and convention findings. Does not run the program. Not a second typechecker — semantic errors stay `elang check`.

- Directory → recursive `*.echo`.
- Finding line: `path:line:col: rule: message`. Any finding → exit 1; clean → silence, exit 0.
- Parse errors match `elang check`.
- No path → help, exit 2. First token must be `lint`; `elang lint.echo` still runs that file.
- Editor task with `--plain` → Problems panel.

| Rule | What it flags |
| --- | --- |
| `unused-local` | declared local, parameter, or loop variable never read |
| `unused-function` | function never called in this file, not exported, and not a zero-arg `test*` entry |
| `unused-import` | imported name never used |
| `comparison-to-bool` | `== true` / `!= false` and the other bool-literal comparisons |
| `redundant-by-one` | explicit `by 1` on `for` (formatter omits it) |
| `empty-block` | empty `if` / `else` body or empty function body |
| `shadow-builtin` | declared name shadows a builtin |
| `test-naming` | top-level `fn` that looks like a test but is not a zero-arg `testXxx` unit |
| `self-assign` | `x = x` or `x = x + 0` / `x = 0 + x` |
| `unreachable-after-fail` | later statement in the same block after `fail(...)` or `return` |

Unused parameters are `unused-local`. `unused-export` and `redundant-parens` are not rules (exports are for other files; grouping parens are not kept on the AST).

## Notes

- The file passed to the CLI is the entry module when it contains `import`.
- Errors are reported by category: syntax, semantic, name, type, argument, index, mutation, or execution.

## See Also

- [Quick Start](/getting-started/quick-start)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
- [Known Limitations](/errors-diagnostics/known-limitations)
