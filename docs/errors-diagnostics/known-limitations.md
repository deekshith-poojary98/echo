# Known Limitations

What Echo still does **not** do. As of **0.9.9**, the language includes modules, CLI tooling, first-class functions, `const` / destructuring / unions / `switch`, nominal classes with `new { ... }` fields (including defaults), bound/unbound/type methods, optional `implements`, interfaces (no inheritance), compound assignment on members, `priv` visibility, positional construction, deep `clone()`, named `format` placeholders, class properties (`get` / `set`), recursive `mkdirAll` / `removeTree`, regex builtins, union narrowing in `if type(...)`, and thin UTC dates (`formatTime` / `parseTime` / duration helpers). This page is the remainder — not a changelog.

## Already in (summary)

- Core syntax and v0.3 file modules (`import` / `export`)
- Host/stdlib, REPL, `check` / `test` / `fmt` / `lint`
- 0.6–0.7: lambdas, collection helpers, `const`, destructuring, exact objects, unions, `switch`, range-as-value
- 0.8: `class` + `new { ... }`, methods + `this`, unbound/type methods, `interface`, optional `implements`
- 0.9.0: compound assignment on class fields (`this.x += 1`)
- 0.9.1: `priv` on fields and methods (class-private)
- 0.9.2: positional construction `Point(3, 4)` (named `Point { ... }` still works)
- 0.9.3: deep `clone()` for lists, hashes, and class instances
- 0.9.4: named `format()` placeholders via trailing hash
- 0.9.5: class properties `get` / `set` (soft keywords; field-style access)
- 0.9.6: `mkdirAll(path)` / `removeTree(path)` for recursive create/delete
- 0.9.7: `regexMatch` / `regexFind` / `regexReplace` / `regexSplit` (Python `re`)
- 0.9.8: union narrowing in `if type(x) == "..."` (and matching `else if`)
- 0.9.9: `formatTime` / `parseTime` (UTC) plus `days` / `hours` / `minutes`

Details: [Roadmap](/project/roadmap) and `CHANGELOG.md`.

## Current Limitations

- No class inheritance (`extends`); shared behavior is interfaces + composition
- No generics
- No exceptions such as `try/catch` — abort stays the default; recovery is inquiry and `*Or` twins ([failure model](/failure-model)). `echo test` may continue after `expect*` failures; that is runner-only, not in-language recovery
- No overloads
- Function scope is lexical; reassignment of outer variables still requires `use mut`
- Nested collections inside a frozen list/hash are not recursively frozen; a nested value reached through a different mutable name can still be mutated
- Open object type aliases accept extra fields; use `exact { ... }` to reject them
- `null` is not a type — use `str | void` when a binding may hold `null`. Full flow-sensitive typing beyond simple-name `if type(...)` guards is not implemented
- Hash runtime indexing only supports string keys
- `format()` has no width / precision / alignment specs
- Properties are not part of interfaces (`implements` still checks methods only)
- Interpolation tokenization is not fully strict
- No date object type / local-timezone calendars (UTC unix seconds + `formatTime` / `parseTime` only); no HTTP builtins
- No LSP (the editor extension runs CLI tasks into the Problems panel; that is not a language server)

## Why this page exists

So docs do not oversell the language, and so shipped work is not mistaken for missing.

## Where next work is tracked

See [Failure model](/failure-model), [Roadmap](/project/roadmap), and [priority](/project/priority).
