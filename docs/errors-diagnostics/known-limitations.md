# Known Limitations

## Overview
This page lists the current limits of Echo as implemented today.

## Current Limitations
- No module or import system for Echo source files
- No classes or user-defined structs
- No generics
- No exceptions such as `try/catch`
- No default parameter values
- No variadic functions
- No overloads
- Function scope is strict and requires `use` / `use mut` for outer variables
- `for ... by 0` is not guarded
- Object type aliases accept extra fields
- Number literal grammar does not support forms like `.5` or `1e3`
- Hash runtime indexing only supports string keys
- `clone()` is shallow
- `format()` only supports positional placeholders
- Interpolation tokenization is not fully strict

## Why This Page Exists
Echo is still evolving. The docs should not make the language sound more complete than it is.

## Planned Improvement
See [Roadmap / Planned Improvements](/project/roadmap) for likely next steps.
