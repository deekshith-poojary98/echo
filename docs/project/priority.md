# Echo remaining-feature priority

Language syntax is frozen at the v0.4 line. Current released version is **v0.4.3**.
This list tracks stdlib/host work only. Do not add held syntax.

Status values: `pending` / `in progress` / `implemented (version)` / `held`.

## Implement now (stdlib/host, no syntax)

| # | Item | Status |
| --- | --- | --- |
| 1 | File mutation: `mkdir(path)`, `removeFile(path)` | implemented (0.4.3) |
| 2 | String position: `indexOf(part)` / `lastIndexOf(part)` | implemented (0.4.3) |
| 3 | String extras: `repeat(n)`, `padStart` / `padEnd`, `replaceFirst` | implemented (0.4.3) |
| 4 | Numbers: `abs`, `min`, `max`, `floor`, `ceil` | implemented (0.4.3) |
| 5 | `eprint(...)` — `say` to stderr | implemented (0.4.3) |

### 1. File mutation

`mkdir(path)` and `removeFile(path)`. Restricted host denies both (E2801). Path must be `str`.

Decisions:

- `mkdir` creates the leaf directory only. Missing parent aborts. Existing path (file or directory) aborts.
- `removeFile` deletes a file. Missing file and directories abort (no silent success).
- Recursive create (`mkdir -p`), recursive delete, and `copyFile` stay held.

### 2. String position

`indexOf(part)` / `lastIndexOf(part)` on strings. `part` must be `str` (E2814-style type error). Missing → `-1`. Empty part → `0` / length. Mirrors list `find` returning `-1`.

### 3. String extras

- `repeat(n)` — `n` is `int`, reject `bool`, `n >= 0`.
- `padStart(width, fill)` / `padEnd(width, fill)` — `width` is `int` (not `bool`), `fill` is a non-empty `str`. If already `>= width`, return the original.
- `replaceFirst(old, new)` — `old` is a non-empty `str`.

### 4. Numbers

`abs(n)`, `floor(n)`, `ceil(n)`, `min(a, b)`, `max(a, b)`. Reject `bool`. `min` / `max` take two numeric args (`int` / `float`), not a list.

### 5. stderr print

Name: `eprint(...)`. Variadic like `say`. No keyword args. Writes to stderr.

## Hygiene (after at least items 1–2)

| # | Item | Status |
| --- | --- | --- |
| 6 | Update `docs/errors-diagnostics/known-limitations.md` for modules / `echo check` / host stdlib | implemented (0.4.3) |

## Held (do not implement)

| Item | Status |
| --- | --- |
| User-level failure recovery | held — design only |
| Formatter, REPL, `echo test`, LSP | held |
| Dates, HTTP, regex | held |
| `mkdir -p` / recursive delete / `copyFile` | held — after mkdir+removeFile if needed |
| Slice syntax `xs[1:4]` | held |
| `try` / `catch` | held |
| First-class functions | held |
| Classes | held |
| Packages | held |
| VM / JIT | held |
| Generics | held |
| Async | held |
| Default / variadic user args | held |
| Overloading | held |
| `map` / `filter` | held |
