# Changelog

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
