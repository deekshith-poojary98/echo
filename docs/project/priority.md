# Echo remaining-feature priority

Current released version is **v0.5.8**. This list is language basics: a few host/stdlib builtins plus two syntax extensions the user asked for. **0.5.8** adds a small `echo lint` rule batch (`test-naming`, `self-assign`, `unreachable-after-fail`). **0.5.7** wires `echo check` / `fmt` / `lint` / `test` into the VS Code/Cursor extension as tasks and Problems matchers (not an LSP). **0.5.6** ships the native `echo test` product (`expect*` helpers, file/function units, summary). **0.5.5** ships `fail(message)` and `echo lint`. **0.5.4** ships `echo fmt`. **0.5.3** ships `readFileOr`, `parseJsonOr`, `asIntOr`, and `asFloatOr`. **0.5.2** makes the REPL keep session state across submissions. **0.5.1** hardened the 0.5.0 CLI (REPL continuation/quit, `echo test` semantics) and playground `allow_run` host enforcement.

Status values: `pending` / `in progress` / `implemented (version)` / `held`.

## Implement now

| # | Item | Status |
| --- | --- | --- |
| 1 | `assert(cond, message)` | implemented (0.5.0) |
| 2 | `copyFile(src, dest)` + `pathJoin(...)` | implemented (0.5.0) |
| 3 | `run(command, args)` | implemented (0.5.0) |
| 4 | `now()` — unix time as `int` seconds | implemented (0.5.0) |
| 5 | `random()` / `randomInt(min, max)` | implemented (0.5.0) |
| 6 | Multiline strings `"""` / `'''` | implemented (0.5.0) |
| 7 | Number literals `.5` and `1e3` / `1e-3` | implemented (0.5.0) |
| 8 | `readLine()` | implemented (0.5.0) |
| 9 | REPL (`echo` with no file) | implemented (0.5.2) |
| 10 | `echo test` product | implemented (0.5.6) |
| 11 | `fail(message)` | implemented (0.5.5) |
| 12 | `echo lint` | implemented (0.5.5), expanded (0.5.8) |
| 13 | `expect` / `expectEq` / `expectNeq` | implemented (0.5.6) |
| 14 | Editor tasks + problem matchers | implemented (0.5.7) |

### 1. `assert(cond, message)`

Abort with an Echo error if `cond` is falsy. `message` must be `str`. No Python `AssertionError` leaks. Analyzer: min 2 standalone args.

### 2. `copyFile` + `pathJoin`

`copyFile(src, dest)` is a UTF-8-agnostic binary copy of a file (not a directory). Restricted host (`allow_files=False`) denies with E2801. Missing src aborts. Missing dest parent aborts. Overwriting dest overwrites the file; abort if dest is a directory.

`pathJoin` takes 2+ string parts (variadic like `say`). Uses pathlib join, not string concat. Restricted host: `pathJoin` stays available (pure path strings; no files).

### 3. `run(command, args)`

`command` is `str`. `args` is a list of `str` (empty list allowed). Returns `{ "code": int, "stdout": str, "stderr": str }`. No `shell=True`. `Host.allow_run: bool = True` by default; playground sets `allow_run=False`. Denied run → E2801-style “not available in this host”. Non-zero exit is not an Echo error. Missing executable is an Echo error.

### 4. `now()`

No arguments. Returns unix time as `int` seconds.

### 5. `random` / `randomInt`

`random()` → float in `[0, 1)`. `randomInt(min, max)` inclusive integers, reject `bool`, require `min <= max`. Python `random`.

### 6. Multiline strings

Triple-quote `"""` and `'''`. Interpolation `${...}` works, matching `"..."` / `'...'`. Newlines are allowed only in triples; single-line quotes stay single-line.

### 7. Number literals

`.5` and scientific `1e3` / `1e-3`. Keep existing `5.` as integer then `.` (method calls like `5.asInt()` stay valid).

### 8. `readLine()`

Read one line from stdin with no required prompt. EOF aborts with an Echo error.

### 9. REPL

`echo` with no file enters a REPL. Keep `echo check` and `echo file.echo`. `--plain` supported.

Harden 0.5.1: brace-depth and unterminated-triple continuation (`... `), empty lines ignored, `exit(code)` / EOF quit without a traceback, one failed submission does not kill the process.

**0.5.2 REPL session state (done):** one Interpreter and Environment for the process. Analyzer-visible declarations persist across successful submissions, so a `fn` or variable defined at one `echo>` is usable at the next. Failed submissions do not drop earlier bindings. `import` loads sibling modules from the working directory into the session. `use mut` works for names declared earlier in the session.

### 10. `echo test`

`echo test [paths...]` is the native runner (0.5.6). No test DSL. No `test "name" { }` keyword.

A directory argument recursively runs `*_test.echo` files. An explicit file path always runs. No path prints help and exits 2. The first argv token `test` is the subcommand; `echo test.echo` still runs that file.

Zero-argument top-level `fn testXxx()` functions are separate units. Remaining top-level statements run once as setup, or as the file unit when there are no such functions. Exit 0 if every unit passed; 1 if any failed.

Harden 0.5.1: no path → help and exit 2; missing file → non-zero Echo error; `exit(2)` fails the unit; `exit(0)` passes; imported modules execute (unlike `check`).

### 11. `fail(message)`

Abort with an Echo error. `message` must be `str`. Same diagnostic family as `assert` (code **E2825**). Always abort. No `*Or` twin. Required message so scripts stay explicit.

### 12. `echo lint`

Style and convention findings, not a second typechecker. `echo lint [paths...]` walks files or recursive `*.echo` directories. Findings exit 1; clean exit 0; no path prints help and exits 2; parse errors match `echo check`. The first token `lint` is the subcommand; `echo lint.echo` still runs that file.

Rules: `unused-local`, `unused-function`, `unused-import`, `comparison-to-bool`, `redundant-by-one`, `empty-block`, `shadow-builtin`, `test-naming`, `self-assign`, `unreachable-after-fail`. Zero-arg `fn test*` entries are not unused-function (the test runner calls them). `test-naming` flags a top-level `fn` that looks like a test (`test*` / `Test*`) but is not a zero-arg `testXxx` unit. Unused parameters stay `unused-local`. `unused-export` is skipped (exports are for importers; no file-local convention). `redundant-parens` is skipped (the AST does not keep grouping parentheses).

### 13. `expect` / `expectEq` / `expectNeq`

Test-only continue-after-failure helpers. `message` must be `str`. `expect(cond, message)` requires `cond` to be `bool`. Under `echo test` a false/mismatch **records** and the unit continues. Outside `echo test` they abort like `assert`. `assert` / `fail` still abort. Codes **E2826** / **E2827** / **E2828**.

### 14. Editor tasks + problem matchers

VS Code / Cursor integration in `echo-syntax-highlighter/`: Run Task / command palette for `echo check`, `echo fmt`, `echo lint`, and `echo test`, with problem matchers into the Problems panel. Tasks use `--plain`. Not an LSP: no completions, jump-to-definition, or language-server diagnostics.

## Held (do not implement)

| Item | Status |
| --- | --- |
| Classes | held |
| Generics | held |
| Async | held |
| VM / JIT | held |
| Packages | held |
| `try` / `catch` | held |
| First-class `map` / `filter` | held |
| User-level failure recovery | designed ([failure model](/failure-model)) — syntax held; `*Or` stdlib implemented (0.5.3) |
| First-class functions | held |
| Slice syntax `xs[1:4]` | held |
| Default / variadic user args | held |
| Overloading | held |
| Formatter / `echo fmt` | implemented (0.5.4) |
| Linter / `echo lint` | implemented (0.5.5), expanded (0.5.8) |
| Native test runner / `echo test` | implemented (0.5.6) |
| Editor tasks + Problems matchers | implemented (0.5.7) |
| LSP | held |
| Dates, HTTP, regex | held |
| `mkdir -p` / recursive delete | held |
