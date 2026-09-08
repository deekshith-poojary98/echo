# Known Limitations

## Overview
This page lists the current limits of Echo as implemented today.

## Current Limitations
- No classes or user-defined structs
- No generics
- No exceptions such as `try/catch`
- No default parameter values
- No variadic user functions
- No overloads
- Function scope is lexical; reassignment of outer variables still requires `use mut`
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
