# Known Limitations

What Echo still does **not** do. As of recent 0.5–0.7 releases, a lot already shipped — this page is the remainder, not a history of the empty interpreter.

Already in:

- Frozen v0.2 language syntax, plus v0.3 file-based modules (`import` / `export`)
- Multiline `"""` / `'''` strings and `.5` / scientific number literals
- Host and stdlib (`args`, `env`, files, JSON, string/list helpers, numeric helpers, `assert`, `expect` / `expectEq` / `expectNeq`, `fail`, `run`, `now`, `random`)
- `echo check [paths...]`, REPL (`echo` with no file), `echo test [paths...]`, `echo fmt`, `echo lint` (`test-naming`, `self-assign`, `unreachable-after-fail` in 0.5.8; multi-path `check` in 0.5.9)
- First-class functions including lambdas, slice syntax `xs[1:4]`, and user `fn` defaults/variadics (0.6.0)
- List `map` / `filter` (0.6.1)
- List `reduce` (0.6.2)
- List `forEach` (0.6.3)
- List `flatMap` (0.6.4)
- List `some` / `every` / `findIndex` (0.6.5)
- Optional slice bounds `xs[1:]` / `xs[:4]` / `xs[:]` (0.6.6)
- List `zip` / `unique` (0.6.7)
- `echo test -run`, list `chunk`, `rangeList` / `rangeListInclusive`, hash `mapValues` / `filter` (0.6.8)
- Function types honor trailing defaults, list `flatten` / `partition`, `echo test --json` (0.6.9)
- `const` bindings (`const name: T = expr;`, `export const`, frozen lists/hashes) (0.7.0)
- Destructuring (`[a: int, b: int] = pair;`, `{ id: int, name: str } = user;`, rest, assignment, fn params) (0.7.1)
- Exact object types (`exact { id: int, name: str }`) (0.7.2)
- Builtins as values (`say`, `map`, bound `xs.map`, …) (0.7.3)
- Range expressions `0...10` / `0..10` (optional `by`) as `list` values (0.7.4)
- Union types `int | str` (0.7.5); not Option; no `null` type member
- `switch` on values (0.7.6); no expression-form `switch`; no `match` / `Result` form
- Hash destructure rename `{ id as userId: int }` (0.7.7)
- Hash destructure rest `{ id: int, rest: dynamic... }` (0.7.8)
- No control-flow narrowing via `if type(x) == "..."` yet (type arms on `switch` cover the main case)

Still out of scope. Classes, `try`/`catch`, and the other frozen holds are not implemented.

## Current Limitations
- No classes or user-defined structs
- No generics
- No exceptions such as `try/catch` — abort stays the default; recovery is inquiry and `*Or` twins ([failure model](/failure-model)). `echo test` may continue after `expect*` failures; that is runner-only, not in-language recovery
- No overloads
- Function scope is lexical; reassignment of outer variables still requires `use mut`
- `const` does not apply to function parameters in 0.7.0 (parameters stay mutable unless a later version adds param `const`)
- Nested collections inside a frozen list/hash are not recursively frozen; a nested value reached through a different mutable name can still be mutated
- Destructuring rename and hash rest ship in 0.7.7 / 0.7.8
- Open object type aliases accept extra fields; use `exact { ... }` to reject them
- Union types do not narrow in `if type(x) == "..."`; `switch` is 0.7.6. `null` is not a type — use `str | void` when needed
- Hash runtime indexing only supports string keys
- `clone()` is shallow
- `format()` only supports positional placeholders
- Interpolation tokenization is not fully strict
- No `mkdir -p` or recursive delete
- No dates, HTTP, or regex builtins
- No LSP (the editor extension runs CLI tasks into the Problems panel; that is not a language server)

## Why this page exists

So docs do not oversell the language, and so shipped work is not mistaken for missing.

## Where next work is tracked

See [Failure model](/failure-model), [Roadmap](/project/roadmap), and [priority](/project/priority).
