# Known Limitations

## Overview
This page lists what Echo still does **not** do. It is not a description of an early pre-module interpreter.

As of v0.5.0, Echo already has:

- Frozen v0.2 language syntax, plus v0.3 file-based modules (`import` / `export`)
- Multiline `"""` / `'''` strings and `.5` / scientific number literals
- A host and standard library (`args`, `env`, files, JSON, string/list helpers, numeric helpers, `assert`, `expect` / `expectEq` / `expectNeq`, `fail`, `run`, `now`, `random`)
- `echo check`, a REPL (`echo` with no file), `echo test [paths...]`, `echo fmt`, and `echo lint`

The items below are still out of scope. Classes, `try`/`catch`, first-class functions, and the other frozen holds are not implemented.

## Current Limitations
- No classes or user-defined structs
- No generics
- No exceptions such as `try/catch` — abort stays the default; recovery is inquiry and `*Or` twins ([failure model](/failure-model)). `echo test` may continue after `expect*` failures; that is runner-only, not in-language recovery
- No default parameter values
- No variadic user functions (`say` / `eprint` / `format` / `pathJoin` are the variadic builtins)
- No overloads
- No first-class function values
- Function scope is lexical; reassignment of outer variables still requires `use mut`
- Object type aliases accept extra fields
- Hash runtime indexing only supports string keys
- `clone()` is shallow
- `format()` only supports positional placeholders
- Interpolation tokenization is not fully strict
- No `mkdir -p` or recursive delete
- No dates, HTTP, or regex builtins
- No LSP

## Why This Page Exists
Echo is still evolving. The docs should not make the language sound more complete than it is, and they should not hide capabilities that already shipped.

## Planned Improvement
See [Failure model](/failure-model), [Roadmap / Planned Improvements](/project/roadmap), and [priority tracking](/project/priority) for remaining stdlib work versus held syntax.
