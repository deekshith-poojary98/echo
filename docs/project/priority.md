# Echo remaining-feature priority

Current released version is **v0.5.1**. This list is language basics: a few host/stdlib builtins plus two syntax extensions the user asked for. **0.5.1** hardens the 0.5.0 CLI (REPL continuation/quit, `echo test` semantics) and playground `allow_run` host enforcement. No new language features.

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
| 9 | REPL (`echo` with no file) | implemented (0.5.0) |
| 10 | `echo test path.echo` | implemented (0.5.0) |

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

`echo` with no file enters a REPL. Keep `echo check` and `echo file.echo`. `--plain` supported. Simple loop: read, `run_source`, print.

Harden 0.5.1: brace-depth and unterminated-triple continuation (`... `), empty lines ignored, `exit(code)` / EOF quit without a traceback, one failed submission does not kill the process. Bindings still do not persist across submissions.

### 10. `echo test`

`echo test path.echo` runs a file; exit 0 is pass. No test DSL.

Harden 0.5.1: no path → help and exit 2; missing file → non-zero Echo error; `exit(2)` fails the test; `exit(0)` passes; imported modules execute (unlike `check`).

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
| User-level failure recovery | held — design only |
| First-class functions | held |
| Slice syntax `xs[1:4]` | held |
| Default / variadic user args | held |
| Overloading | held |
| Formatter / LSP | held |
| Dates, HTTP, regex | held |
| `mkdir -p` / recursive delete | held |
