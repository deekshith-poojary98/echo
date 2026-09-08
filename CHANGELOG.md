# Changelog

## 0.4.0

Host and standard-library cut. No new syntax.

- `args()`, `env()`, `envOr()`, `readFile()`, `writeFile()`, `parseJson()`, `writeJson()`
- String/list `split`, `replace`, `contains`, `slice`; hash `has`
- `asInt` / `asFloat` reject `bool` (semantic correction)
- Failures still abort with Echo errors; playground denies files
- Not included: slice syntax, `try/catch`, function values, classes

## 0.3.0

File-based modules on top of the frozen v0.2.1 language.

- `import name from "module"` and `export` are the only module syntax
- Sibling `.echo` files resolve by bare name; `.echo` is implied
- Exports are explicit; imports are selective and flatten into module scope
- Imported bindings are immutable; imported collections share identity
- `use` / `use mut` keep their v0.2.1 meaning and never load modules
- Same-module writes still require `use mut` (no module-owned-state exception)
- Circular dependencies are rejected before any module initializes
- A program with no `import` keeps the single-file pipeline

## 0.2.1

Semantic cleanup under the frozen v0.2 pipeline.

- User-function keyword arguments are validated by the semantic analyzer
- Builtin arity checks for required standalone calls
- `foreach` only accepts lists and hashes
- `for` bounds reject `bool` and other non-numeric values
- `order()` of mixed types is an Echo type error
- Index assignment uses Echo index errors, not Python exceptions
- Error categories distinguish argument, index, and mutation errors

## 0.2.0

Architecture and correctness release.

- Documented language semantics
- Typed AST, semantic analyzer, and split runtime
- Lexical scoping and nested-block `use mut`
- Distinct `null` lookup and `bool` vs `int`
- Source locations and Echo error types
- Builtins removed from the lexer
- CLI `--version`
- Correctness fixes for comments, interpolation, `reverse`, `find`, `format`, `wait`, and `asInt`
