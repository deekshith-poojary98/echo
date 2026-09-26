# Echo failure model

> **Status:** Frozen. `*Or` twins shipped in v0.5.3.
> **Rule:** Abort by default. Recovery is inquiry and `*Or` twins — not `try` / `catch`.
> **Background:** [v0.4 language vs stdlib](/archive/v0.4-language-vs-stdlib) section 8

How Echo fails. This page does not add grammar.
`try` / `catch`, `Result` / `Option`, and `?` stay held.

---

## Default

```text
operation
  success → value
  failure → EchoError → abort (CLI exit 1)
```

That is the default for host and stdlib builtins.

Exceptions already shipped (this note does not change them):

- Inquiry: `fileExists`, `isDir`, `has`, `contains`, `find` (`-1`)
- Fallback twin: `envOr(name, fallback)`, `readFileOr(path, fallback)`, `parseJsonOr(text, fallback)`, `asIntOr(value, fallback)`, `asFloatOr(value, fallback)`, `httpGetOr` / `httpPostOr` (1.1.1)
- Status value: `run` → `{ "code", "stdout", "stderr" }` (non-zero is not an Echo error)
- Programmer abort: `assert(cond, message)`, `fail(message)`, `exit(code)`
- Test-only continue: `expect` / `expectEq` / `expectNeq` under `echo test` (0.5.6). They record and continue in that runner; outside `echo test` they abort like `assert`. This is not `try` / `catch` and not user-level recovery.
- Host policy: `allow_files=False` / `allow_run=False` / `allow_http=False` always abort (`E2801`)
- HTTP status: non-2xx from `httpGet` / `httpPost` still returns the response hash (not an Echo error)

`default()` is truthiness. It is not error handling. Do not overload it.

---

## Three classes

Do not mix these.

### 1. Bugs — always abort

Contract violations. Not recoverable. No `*Or` twin.

- Type errors, arity, keyword mistakes
- Index out of range (`xs[i]`, `slice` bounds, `pull` on empty)
- Missing hash key via `user["x"]`
- Host denied (`E2801`)
- Missing executable for `run`
- `assert` failure
- `fail(message)` — assert-without-condition; always abort; code `E2825`
- `expect` / `expectEq` / `expectNeq` type errors (non-`bool` condition, non-`str` message) — always abort; codes `E2826` / `E2827` / `E2828`
- `asInt(true)` / `asFloat(true)` — bool has no twin

Catching these would hide bugs.

`expect*` false/mismatch is a test assertion, not language recovery. Only `echo test` continues after it, and only for that helper. `assert` / `fail` still abort the current test unit.

### 2. Expected absence — check or fallback

The program may continue. Two shapes, pick on purpose.

**Inquiry** when presence is the question:

```echo
if fileExists("notes.txt") {
    text: str = readFile("notes.txt");
}
```

**Fallback twin** when a default is enough (same shape as `envOr`):

```echo
home: str = envOr("HOME", "");
text: str = readFileOr("notes.txt", "");
data: dynamic = parseJsonOr(text, null);
n: int = asIntOr(raw, 0);
```

Shipped in 0.5.3: `readFileOr`, `parseJsonOr`, `asIntOr` / `asFloatOr` for untrusted input. Same rules as `envOr`:

- Success → the real value
- Expected failure → `fallback` (any Echo value)
- Wrong argument types still abort
- Host deny still aborts
- `asIntOr(true, 0)` / `asFloatOr(true, 0.0)` still abort — bool is a bug, not untrusted input
- `default()` is not this

Do **not** change `readFile` to return a hash or `null` on failure. The aborting name stays the default.

### 3. Status values — already a value

`run` returns `{ "code", "stdout", "stderr" }`. Non-zero exit is not an Echo error. Do not wrap it. Do not invent `try` for it.

`find` → `-1` is a sentinel, not an error. Do not turn it into abort or `Result`.

---

## Design Q&A (from section 8)

**Bugs vs expected.** File-not-found, unset env, and invalid JSON-from-text are expected. `notes[99]` and `asInt(true)` are bugs. Trusted `parseJson` may stay abort; untrusted text uses `parseJsonOr`.

**Can a user `fn` fail like a builtin?** No catchable form. It returns a value or aborts (`assert`, `fail(message)`). Recoverable user APIs return an ordinary hash (`{ "ok": true, "value": x }`) — a convention for that function, not a language `Result`, and not something builtins must adopt.

**In-language recovery or hash-in-caller?** Builtins: named twins and inquiry only, not control-flow. User functions may return a hash. A global `{ ok, value, error }` from every builtin is rejected.

**What does `watch` print on a handled failure?** Abort never assigns, so `watch` does not run. An `*Or` / `envOr` fallback is a normal value; `watch` prints it like any other assignment.

---

## Rejected (held)

- `try` / `catch` / `finally` — hides which ops fail
- `Result` / `Option`, `?`, `match` — type-system revision
- Aborting builtins returning `null` on failure — silent bugs
- Overloading `default()` for errors

---

## Shipped stdlib twins (0.5.3 + 1.1.1)

`readFileOr`, `parseJsonOr`, `asIntOr`, `asFloatOr` (0.5.3). `httpGetOr` / `httpPostOr` (1.1.1). Builtins only — not a language revision.

| Twin | Fallback | Still abort |
| --- | --- | --- |
| `readFileOr(path, fallback)` | missing file, invalid UTF-8, directory, other read OSError that `readFile` reports as cannot-read | host deny (`E2801`); non-`str` path |
| `parseJsonOr(text, fallback)` | invalid JSON | non-`str` text |
| `asIntOr(value, fallback)` / `asFloatOr(value, fallback)` | unparseable `str`, `null`, list, hash, and other “cannot convert” values | `bool` (no twin); success still returns the number |
| `httpGetOr` / `httpPostOr` | network / timeout / invalid or empty URL (`E2852` runtime) | host deny (`E2801`); type errors (`E2852` type) |

---

## See also

- [v0.4 language vs stdlib](/archive/v0.4-language-vs-stdlib) (historical)
- [v0.4 standard library](/archive/v0.4-stdlib) (historical)
- [Language semantics](/language-semantics)
- [Known limitations](/errors-diagnostics/known-limitations)
- [Priority](/project/priority)
