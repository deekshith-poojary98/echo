# Known Limitations

## Overview
This page lists what Echo still does **not** do. It is not a description of an early pre-module interpreter.

As of v0.4.3, Echo already has:

- Frozen v0.2 language syntax, plus v0.3 file-based modules (`import` / `export`)
- A host and standard library (`args`, `env`, files, JSON, string/list helpers, numeric helpers)
- `echo check` for analyze-without-execute

The items below are still out of scope. Classes, `try`/`catch`, first-class functions, and the other frozen holds are not implemented.

## Current Limitations
- No classes or user-defined structs
- No generics
- No exceptions such as `try/catch` — host and stdlib failures abort with Echo errors
- No default parameter values
- No variadic user functions (`say` / `eprint` / `format` are the variadic builtins)
- No overloads
- No first-class function values
- Function scope is lexical; reassignment of outer variables still requires `use mut`
- Object type aliases accept extra fields
- Number literal grammar does not support forms like `.5` or `1e3`
- Hash runtime indexing only supports string keys
- `clone()` is shallow
- `format()` only supports positional placeholders
- Interpolation tokenization is not fully strict
- No `mkdir -p`, recursive delete, or `copyFile`
- No dates, HTTP, or regex builtins
- No formatter, REPL, `echo test` runner, or LSP

## Why This Page Exists
Echo is still evolving. The docs should not make the language sound more complete than it is, and they should not hide capabilities that already shipped.

## Planned Improvement
See [Roadmap / Planned Improvements](/project/roadmap) and [priority tracking](/project/priority) for remaining stdlib work versus held syntax.
