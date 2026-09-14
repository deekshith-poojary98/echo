# Roadmap

Short pointer. The ordered plan lives in [Priority](/project/priority). This page is not a promise list.

## Shipped (do not re-list as “later”)

Already in the language or CLI:

- File modules: `import` / `export` (v0.3)
- REPL (`echo` with no file), `echo check`, `echo test`, `echo fmt`, `echo lint`
- Exact object types: `exact { ... }` (0.7.2)
- Number literals `.5` / scientific form; multiline strings
- `const`, destructuring (hash `as` rename in 0.7.7), builtins as values, range-as-value, unions (`int | str`), `switch` through 0.7.7

## Next

Optional 0.7 polish, then held 0.8 OOP:

| Version | Item | Status |
| --- | --- | --- |
| 0.7.8 | Hash rest | pending |
| 0.7.9 | Param `const` | pending |
| 0.8.0–0.8.2 | OOP (`class` / methods / `interface`) | held (draft) |

Details and spellings: [Priority — 0.8.x](/project/priority).

## Held

Not near-term. Do not treat these as upcoming releases unless a draft series exists above:

- Generics, async, VM / JIT, packages
- `try` / `catch`, `Result` / `Option`, user-level recovery syntax
- Overloading, LSP
- Dates / HTTP / regex builtins
- `mkdir -p` / recursive delete
- Test DSL (`test "name" { }`)
- Class inheritance (out of 0.8; interfaces only in the draft)

See [Known Limitations](/errors-diagnostics/known-limitations) and [failure model](/failure-model).

## See Also

- [Priority](/project/priority)
- [Known Limitations](/errors-diagnostics/known-limitations)
- [CLI and Execution Model](/reference/cli-and-execution-model)
