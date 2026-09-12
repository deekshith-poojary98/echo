# Echo remaining-feature priority

Current tagged version is **v0.6.2**. **0.5.9** closed the 0.5.x tooling arc; **0.6.0** ships first-class functions (including lambdas), slice syntax, and user `fn` defaults/variadics; **0.6.1** adds list `map` / `filter`; **0.6.2** adds list `reduce`; **0.6.3** adds list `forEach`. **0.6 continues through 0.6.9** — six pending increments below. **0.7 starts only after 0.6.9 has shipped.** `const` / destructuring stay **0.7**, not late 0.6.

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

**0.5.9** closed the 0.5.x tooling arc. **0.6** opens language. **Policy: do not start 0.7 until Echo has shipped through 0.6.9.** Current tag is **v0.6.2**. Each of **0.6.4–0.6.9** is one shippable increment (same rhythm as 0.5.4–0.6.3): function/collection/language ergonomics plus small stdlib that needs 0.6.0 function values.

**0.6.0** shipped all three language items in **one** release:

1. First-class functions **including lambdas**
2. Slice syntax
3. Default **and** variadic user `fn` args **together**

**0.6.1** ships list `map` / `filter` on the function values from 0.6.0.

**0.6.2** ships list `reduce` on those same function values.

**0.6.3** ships list `forEach` on those same function values.

Failure model is unchanged through 0.6.9: callbacks or default expressions that abort still abort. No `try` / `catch`. No `Result` / `Option`. No extra `*Or` twins in this stretch — the 0.5.3 set still covers the designed recovery cases.

Already shipped, so **not** re-proposed: `args` / `env` / files / JSON / `fmt` / `lint` / `test` / `check` / `map` / `filter` / `reduce` / `forEach` / `slice()` / `xs[1:4]` / lambdas / defaults / variadics / `order(comparator)` / `find(value)` / `reverse` / `contains`.

Held items below stay held for the whole 0.6.4–0.6.9 stretch (VM/JIT, classes, generics, async, packages, try/catch, Result/Option, overloading, LSP, dates/HTTP/regex, `mkdir -p`, test DSL). `const` / destructuring are **0.7**, not 0.6.8/0.6.9.

| Version | Item | Status |
| --- | --- | --- |
| 0.6.0 | First-class functions including lambdas | implemented (0.6.0) |
| 0.6.0 | Slice syntax `xs[1:4]` | implemented (0.6.0) |
| 0.6.0 | Default and variadic user `fn` args | implemented (0.6.0) |
| 0.6.1 | `map` / `filter` | implemented (0.6.1) |
| 0.6.2 | `reduce` | implemented (0.6.2) |
| 0.6.3 | `forEach` | implemented (0.6.3) |
| 0.6.4 | `flatMap` | pending |
| 0.6.5 | `some` / `every` / `findIndex` | pending |
| 0.6.6 | Optional slice bounds `xs[1:]` `xs[:4]` `xs[:]` | pending |
| 0.6.7 | `zip` | pending |
| 0.6.8 | `unique` | pending |
| 0.6.9 | Function types honor defaults | pending |

### 0.6.0 — first-class functions (including lambdas)

Functions are values. Lambda spelling: **`fn(x: int) -> int { ... }`** (inline `=>` also works). Function type spelling: **`fn(int) -> int`**. `order(comparator)` accepts a function value, a lambda, or a name string.

### 0.6.0 — slice syntax

Spelling: **`xs[1:4]`** (colon, not `..`). **Both bounds required** — no `xs[1:]`, `xs[:4]`, or `xs[:]`. Desugars to existing `slice(start, end)` with the same bounds as today: start and end in `[0, length]`, end exclusive, no negatives, out-of-bounds aborts.

### 0.6.0 — default and variadic user `fn` args

User `fn` default arguments and variadic arguments ship **together**. Spelling: **`punct: str = "!"`** and **`parts: int...`** (variadic last, rest is a `list` of `T`). Defaults come before the variadic and are evaluated at call time. Overloading stays held. Function types still spell parameter types only (`fn(int, str) -> int`) and do not yet treat defaulted parameters as optional when assigning (that is **0.6.9**).

### 0.6.1 — `map` / `filter`

List `map(items, f)` / `filter(items, f)` and method form `items.map(f)` / `items.filter(f)`. `filter` requires a `bool` return (`1` is not kept). Callbacks that abort abort the call. No string or hash variants; hashes have no map/filter iteration in this cut.

### 0.6.2 — `reduce`

List `reduce(items, init, f)` / `items.reduce(init, f)`. `f` is `fn(acc, item) -> acc`. `init` is required; empty list returns `init` and does not call `f`. Returns a new value; does not mutate the input. A callback that aborts aborts the call. List only. No second `fold` builtin. Codes: non-function `f` **E2832**, wrong arity **E2833**, callback result type ≠ `init` **E2834**.

### 0.6.3 — `forEach`

List `forEach(items, f)` / `items.forEach(f)`. Unary callback; the return value is discarded. Returns `null`. Does not mutate the input itself (the callback may, under `use mut`). Empty list is a no-op. A callback that aborts aborts the call. List only.

### 0.6.4 — `flatMap`

List `flatMap(items, f)` / `items.flatMap(f)`. Unary `f` must return a `list`; a non-list return is a type error. Concatenates those lists **one** level into a new list. Empty input returns `[]`. Does not mutate the input. A callback that aborts aborts the call. List only.

### 0.6.5 — `some` / `every` / `findIndex`

List predicates on a unary `fn(T) -> bool` (same bool rule as `filter`). `some` is `true` if any element matches (empty → `false`). `every` is `true` if all match (empty → `true`). `findIndex` is the first matching index, or `-1` if none — same sentinel as existing `find(value)`. `find(value)` stays value search; do not overload it. Short-circuit. Method + standalone. List only. Callbacks that abort abort the call.

### 0.6.6 — optional slice bounds

`xs[1:]`, `xs[:4]`, and `xs[:]` parse and desugar to `slice`. Omitted start is `0`; omitted end is `length`. Same abort rules as today for any bound that is present: `[0, length]`, end exclusive, no negatives, out of range aborts. `xs[:]` is `slice(0, length)`. Lists and strings, matching `slice()`. This is why 0.6.x does not also ship `take` / `drop`.

### 0.6.7 — `zip`

Standalone `zip(left, right)` → a new list of 2-element lists `[left[i], right[i]]`. Both arguments must be `list`. Length is `min(len(left), len(right))` (unequal is not an Echo error). Empty either side returns `[]`. Does not mutate the inputs. Two lists only — no N-way zip, no zipper callback (that is `map` after `zip`, or later).

### 0.6.8 — `unique`

List `unique(items)` / `items.unique()` → a new list of first occurrences in original order, using Echo `==`. Does not mutate the input. Empty → `[]`. List only. Not `reverse` (already in-place on lists). Not hash `take`.

### 0.6.9 — function types honor defaults

Closes the 0.6.0 caveat: types still spell **`fn(int) -> int`** (no default markers, no `?`). A function whose trailing parameters have defaults is assignable to a function type that **omits** those parameters, and still to the full-arity type. `fn(x: int, y: int = 0) -> int` matches `fn(int) -> int` and `fn(int, int) -> int`, not `fn() -> int`. Calls through the narrower type pass only those args; the implementation fills defaults at call time. Required parameters and variadics still have to match the type. Not builtins-as-values.

### After 0.6.9 (0.7 — do not start yet)

Not scheduled as 0.6.x, not dummy versions:

- `const` / destructuring (held for 0.7; not stretched into 0.6.8/0.6.9)
- Builtins as assignable values (`say` / `map` as function values — too big for this stretch)
- Exact object types (reject extra fields)
- Range as a value (`0...10` producing a list; loop ranges already exist)
- `echo test -run` / JSON reporter (no test DSL)
- String `map` / `filter` over graphemes (awkward; skipped)

## Held (do not implement)

Do not move these into 0.6.3–0.6.9. `const` / destructuring stay **0.7** (after 0.6.9), not late 0.6.

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
| `const` / destructuring | held (0.7, after 0.6.9) |
