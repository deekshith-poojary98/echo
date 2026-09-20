# Known Limitations

What Echo still does **not** do. As of **0.8.4**, the language includes modules, CLI tooling, first-class functions, `const` / destructuring / unions / `switch`, and nominal classes with `new { ... }` fields (including defaults), methods, and interfaces (no inheritance). This page is the remainder — not a changelog.

## Already in (summary)

- Core syntax and v0.3 file modules (`import` / `export`)
- Host/stdlib, REPL, `check` / `test` / `fmt` / `lint`
- 0.6–0.7: lambdas, collection helpers, `const`, destructuring, exact objects, unions, `switch`, range-as-value
- 0.8: `class` + construction, methods + `this`, `interface`

Details: [Roadmap](/project/roadmap) and `CHANGELOG.md`.

## Current Limitations

- No class inheritance (`extends`); shared behavior is interfaces + composition
- No generics
- No exceptions such as `try/catch` — abort stays the default; recovery is inquiry and `*Or` twins ([failure model](/failure-model)). `echo test` may continue after `expect*` failures; that is runner-only, not in-language recovery
- No overloads
- Function scope is lexical; reassignment of outer variables still requires `use mut`
- Nested collections inside a frozen list/hash are not recursively frozen; a nested value reached through a different mutable name can still be mutated
- Open object type aliases accept extra fields; use `exact { ... }` to reject them
- Union types do not narrow in `if type(x) == "..."`; use `switch` type arms. `null` is not a type — use `str | void` when needed
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
