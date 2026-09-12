# Echo remaining-feature priority

Current released version is **v0.6.1**. **0.5.9** closed the 0.5.x tooling arc; **0.6.0** ships first-class functions (including lambdas), slice syntax, and user `fn` defaults/variadics; **0.6.1** adds list `map` / `filter` (see **0.6.x** below).

The completed 0.5.x work was language basics: a few host/stdlib builtins plus two syntax extensions, then CLI/editor tooling. **0.5.9** is the last 0.5.x slice: `echo check [paths...]` with directory recursion (same as `fmt` / `lint` / `test`) plus editor **Check workspace**. **0.5.8** adds a small `echo lint` rule batch (`test-naming`, `self-assign`, `unreachable-after-fail`). **0.5.7** wires `echo check` / `fmt` / `lint` / `test` into the VS Code/Cursor extension as tasks and Problems matchers (not an LSP). **0.5.6** ships the native `echo test` product (`expect*` helpers, file/function units, summary). **0.5.5** ships `fail(message)` and `echo lint`. **0.5.4** ships `echo fmt`. **0.5.3** ships `readFileOr`, `parseJsonOr`, `asIntOr`, and `asFloatOr`. **0.5.2** makes the REPL keep session state across submissions. **0.5.1** hardened the 0.5.0 CLI (REPL continuation/quit, `echo test` semantics) and playground `allow_run` host enforcement.

Status values: `pending` / `in progress` / `implemented (version)` / `held`.

## Implement now (0.5.x — completed)

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
| 14 | Editor tasks + problem matchers | implemented (0.5.7), Check workspace (0.5.9) |
| 15 | `echo check [paths...]` | implemented (0.5.9) |

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

VS Code / Cursor integration in `echo-syntax-highlighter/`: Run Task / command palette for `echo check`, `echo fmt`, `echo lint`, and `echo test`, with problem matchers into the Problems panel. Tasks use `--plain`. **Echo: Check workspace** (0.5.9) runs `echolang check --plain` on the folder; **Echo: Check file** remains. Not an LSP: no completions, jump-to-definition, or language-server diagnostics.

### 15. `echo check [paths...]`

Last 0.5.x tooling slice. No new language syntax.

`echo check [paths...]` walks files or recursive `*.echo` directories, same collection helper as `fmt` / `lint`. Analyze only; do not run. Exit 0 if every file is clean; 1 if any parse/semantic check fails. After a failure, continue so `echo check .` reports every bad file, then exit 1. Missing path exits 1. No path prints help and exits 2. The first token `check` is the subcommand; `echo check.echo` still runs that file. `--plain` is supported.

## 0.6.x

**0.5.9** closed the 0.5.x tooling arc. **0.6** opens language.

**0.6.0** ships all three language items in **one** release (not split across 0.6.0 / 0.6.1 / 0.6.2):

1. First-class functions **including lambdas**
2. Slice syntax
3. Default **and** variadic user `fn` args **together**

**0.6.1** ships list `map` / `filter` on the function values from 0.6.0.

Failure model is unchanged: callbacks or default expressions that abort still abort. No `try` / `catch`. No `Result` / `Option`.

| # | Item | Status |
| --- | --- | --- |
| 1 | First-class functions including lambdas | implemented (0.6.0) |
| 2 | Slice syntax `xs[1:4]` | implemented (0.6.0) |
| 3 | Default and variadic user `fn` args | implemented (0.6.0) |
| 4 | `map` / `filter` | implemented (0.6.1) |

### 0.6.0 — first-class functions (including lambdas)

Functions are values. Lambda spelling: **`fn(x: int) -> int { ... }`** (inline `=>` also works). Function type spelling: **`fn(int) -> int`**. `order(comparator)` accepts a function value, a lambda, or a name string.

### 0.6.0 — slice syntax

Spelling: **`xs[1:4]`** (colon, not `..`). **Both bounds required** — no `xs[1:]`, `xs[:4]`, or `xs[:]`. Desugars to existing `slice(start, end)` with the same bounds as today: start and end in `[0, length]`, end exclusive, no negatives, out-of-bounds aborts.

### 0.6.0 — default and variadic user `fn` args

User `fn` default arguments and variadic arguments ship **together**. Spelling: **`punct: str = "!"`** and **`parts: int...`** (variadic last, rest is a `list` of `T`). Defaults come before the variadic and are evaluated at call time. Overloading stays held.

### 0.6.1 — `map` / `filter`

List `map(items, f)` / `filter(items, f)` and method form `items.map(f)` / `items.filter(f)`. `filter` requires a `bool` return (`1` is not kept). Callbacks that abort abort the call. No string or hash variants; hashes have no map/filter iteration in this cut.

## Held (do not implement)

Do not move these into 0.6.0. `const` / destructuring stay 0.7+ unless reopened.

| Item | Status |
| --- | --- |
| Classes | held |
| Generics | held |
| Async | held |
| VM / JIT | held |
| Packages | held |
| `try` / `catch` | held |
| `Result` / `Option` | held |
| User-level failure recovery | designed ([failure model](/failure-model)) — syntax held; `*Or` stdlib implemented (0.5.3) |
| Overloading | held |
| Formatter / `echo fmt` | implemented (0.5.4) |
| Linter / `echo lint` | implemented (0.5.5), expanded (0.5.8) |
| Native test runner / `echo test` | implemented (0.5.6) |
| Multi-path `echo check` | implemented (0.5.9) |
| Editor tasks + Problems matchers | implemented (0.5.7), Check workspace (0.5.9) |
| LSP | held |
| Dates, HTTP, regex | held |
| `mkdir -p` / recursive delete | held |
| Test DSL (`test "name" { }`) | held |
| `const` / destructuring | held (0.7+ unless reopened) |
