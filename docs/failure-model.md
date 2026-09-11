# Echo failure model

> **Status:** Frozen design decision. `*Or` stdlib twins shipped in v0.5.3.
> **Theme:** Abort by default. Recovery is inquiry and `*Or` twins, not `try/catch`.
> **Questions answered:** [`docs/v0.4-language-vs-stdlib.md`](/v0.4-language-vs-stdlib) section 8

This is the contract for how Echo fails. It does **not** add grammar.
`try` / `catch`, `Result` / `Option` types, and `?` stay held.

---

## Default

```text
operation
  success → value
  failure → EchoError → abort (CLI exit 1)
```

That is still the honest default for host and stdlib builtins.

Already-shipped exceptions, which this note does not rewrite:

- Inquiry: `fileExists`, `isDir`, `has`, `contains`, `find` (`-1`)
- Fallback twin: `envOr(name, fallback)`, `readFileOr(path, fallback)`, `parseJsonOr(text, fallback)`, `asIntOr(value, fallback)`, `asFloatOr(value, fallback)`
- Status value: `run` → `{ "code", "stdout", "stderr" }` (non-zero is not an Echo error)
- Programmer abort: `assert(cond, message)`, `exit(code)`
- Host policy: `allow_files=False` / `allow_run=False` always abort (`E2801`)

`default()` is truthiness. It is not error handling. Do not overload it.

---

## Three classes

Mixing these is the bug.

### 1. Bugs — always abort

Programmer or contract violations. Never recoverable. No `*Or` twin.

- Type errors, arity, keyword mistakes
- Index out of range (`xs[i]`, `slice` bounds, `pull` on empty)
- Missing hash key via `user["x"]`
- Host denied (`E2801`)
- Missing executable for `run`
- `assert` failure
- `asInt(true)` / `asFloat(true)` — bool has no twin

Catching these would hide bugs.

### 2. Expected absence — check or fallback

The program may continue. Two spells, used on purpose.

**Inquiry first** when presence is the question:

```echo
if fileExists("notes.txt") {
    text: str = readFile("notes.txt");
}
```

**Fallback twin** when a default is the answer, same shape as `envOr`:

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

Do **not** convert `readFile` itself into a hash or `null`. The aborting name stays the honest default.

### 3. Status values — already a value

`run` is the model: the interesting outcome *is* the code. Do not wrap it in Echo errors. Do not invent `try` for it.

`find` → `-1` stays a sentinel, not an error. Do not “fix” it into abort or `Result`.

---

## Answers section 8 required

**Which failures are bugs vs expected.** The table above. File-not-found, unset env, and invalid JSON-from-text are expected. `notes[99]` and `asInt(true)` are bugs. Invalid JSON on `parseJson` of a trusted file can stay abort; untrusted text uses `parseJsonOr`.

**Can a user function produce the same kind of failure a builtin produces?** No catchable form. A user `fn` returns a value or it aborts (`assert`, or a future `fail(message)` as assert-without-condition). Recoverable user APIs return an ordinary hash the author defined (`{ "ok": true, "value": x }`). That is a convention for *that* function, not a language `Result` type and not something builtins must adopt.

**Is recovery in-language, or is hash-in-caller enough?** Recovery for builtins is in-language only as **named twins and inquiry**, not control-flow. Hash-in-caller is allowed for user functions only. A global `{ ok, value, error }` return from every builtin is rejected.

**What does `watch` print when a failure is handled?** Abort never assigns, so `watch` does not run. An `*Or` / `envOr` fallback is a normal value; `watch` prints it like any other assignment. No special “handled failure” output.

---

## Rejected (stay held)

- `try` / `catch` / `finally` — control-flow copy of JS/Java; hides which ops fail
- `Result` / `Option` types, `?`, `match` — type-system revision
- Changing aborting builtins to return `null` on failure — silent bugs
- Overloading `default()` for errors

---

## Shipped stdlib twins (0.5.3)

`readFileOr`, `parseJsonOr`, `asIntOr`, and `asFloatOr` are builtins. They do not open a language revision.

| Twin | Fallback | Still abort |
| --- | --- | --- |
| `readFileOr(path, fallback)` | missing file, invalid UTF-8, directory, other read OSError that `readFile` reports as cannot-read | host deny (`E2801`); non-`str` path |
| `parseJsonOr(text, fallback)` | invalid JSON | non-`str` text |
| `asIntOr(value, fallback)` / `asFloatOr(value, fallback)` | unparseable `str`, `null`, list, hash, and other “cannot convert” values | `bool` (no twin); success still returns the number |

---

## See also

- [v0.4 language vs stdlib](/v0.4-language-vs-stdlib)
- [v0.4 standard library](/v0.4-stdlib)
- [Language semantics](/language-semantics)
- [Known limitations](/errors-diagnostics/known-limitations)
- [Priority](/project/priority)
