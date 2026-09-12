# Known Limitations

## Overview
This page lists what Echo still does **not** do. It is not a description of an early pre-module interpreter.

As of v0.5.0, Echo already has:

- Frozen v0.2 language syntax, plus v0.3 file-based modules (`import` / `export`)
- Multiline `"""` / `'''` strings and `.5` / scientific number literals
- A host and standard library (`args`, `env`, files, JSON, string/list helpers, numeric helpers, `assert`, `expect` / `expectEq` / `expectNeq`, `fail`, `run`, `now`, `random`)
- `echo check [paths...]`, a REPL (`echo` with no file), `echo test [paths...]`, `echo fmt`, and `echo lint` (`test-naming`, `self-assign`, `unreachable-after-fail` added in 0.5.8; multi-path `check` in 0.5.9)
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

The items below are still out of scope. Classes, `try`/`catch`, and the other frozen holds are not implemented.

## Current Limitations
- No classes or user-defined structs
- No generics
- No exceptions such as `try/catch` — abort stays the default; recovery is inquiry and `*Or` twins ([failure model](/failure-model)). `echo test` may continue after `expect*` failures; that is runner-only, not in-language recovery
- No overloads
- Function scope is lexical; reassignment of outer variables still requires `use mut`
- `const` does not apply to function parameters in 0.7.0 (parameters stay mutable unless a later version adds param `const`)
- Nested collections inside a frozen list/hash are not recursively frozen; a nested value reached through a different mutable name can still be mutated
- Object type aliases accept extra fields
- Hash runtime indexing only supports string keys
- `clone()` is shallow
- `format()` only supports positional placeholders
- Interpolation tokenization is not fully strict
- No `mkdir -p` or recursive delete
- No dates, HTTP, or regex builtins
- No LSP (the editor extension runs CLI tasks into the Problems panel; that is not a language server)

## Why This Page Exists
Echo is still evolving. The docs should not make the language sound more complete than it is, and they should not hide capabilities that already shipped.

## Planned Improvement
See [Failure model](/failure-model), [Roadmap / Planned Improvements](/project/roadmap), and [priority tracking](/project/priority) for remaining stdlib work versus held syntax.
