# Roadmap

Short pointer. The ordered plan lives in [Priority](/project/priority). This page is not a promise list.

## Shipped (do not re-list as “later”)

Already in the language or CLI:

- File modules: `import` / `export` (v0.3)
- REPL (`echo` with no file), `echo check`, `echo test`, `echo fmt`, `echo lint`
- Exact object types: `exact { ... }` (0.7.2)
- Number literals `.5` / scientific form; multiline strings
- `const`, destructuring, builtins as values, range-as-value, unions (`int | str`), `switch` through 0.7.6

## Next

| Version | Item | Status |
| --- | --- | --- |
| — | 0.7 spine extras closed through 0.7.6 | — |

Details and spellings: [Priority — 0.7.x](/project/priority).

## Held

Not near-term. Do not treat these as upcoming releases:

- Classes, generics, async, VM / JIT, packages
- `try` / `catch`, `Result` / `Option`, user-level recovery syntax
- Overloading, LSP
- Dates / HTTP / regex builtins
- `mkdir -p` / recursive delete
- Test DSL (`test "name" { }`)

See [Known Limitations](/errors-diagnostics/known-limitations) and [failure model](/failure-model).

## See Also

- [Priority](/project/priority)
- [Known Limitations](/errors-diagnostics/known-limitations)
- [CLI and Execution Model](/reference/cli-and-execution-model)
