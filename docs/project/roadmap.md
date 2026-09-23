# Roadmap

Public status page for what ships today. The ordered implementation plan lives under Internals → [Priority](/project/priority). This page is not a promise list.

## Shipped (do not re-list as “later”)

Already in the language or CLI:

- File modules: `import` / `export` (v0.3)
- REPL (`echo` with no file), `echo check`, `echo test`, `echo fmt`, `echo lint`
- Exact object types: `exact { ... }` (0.7.2)
- Number literals `.5` / scientific form; multiline strings
- `const` (including param `const` in 0.7.9), destructuring (hash `as` rename, hash rest), builtins as values, range-as-value, unions (`int | str`), `switch` through 0.7.9
- Nominal `class` + construction (0.8.0); methods + `this` (0.8.1); `interface` (0.8.2); explicit `new { ... }` fields (0.8.3); field defaults (0.8.4); unbound methods (0.8.5); type methods (0.8.6); optional `implements` (0.8.7); docs/README release pass (0.8.8); first PyPI package `echolang` (0.8.9)
- Compound assign on class members (`this.x += 1`) (0.9.0); `priv` fields/methods (0.9.1); positional construction `Point(3, 4)` (0.9.2); deep `clone()` (0.9.3); named `format` placeholders (0.9.4); class properties `get`/`set` (0.9.5); `mkdirAll` / `removeTree` (0.9.6); regex builtins (0.9.7); union narrowing in `if type(...)` (0.9.8); thin dates `formatTime` / `parseTime` / duration helpers (0.9.9)
- Stable release **1.0.0** (same surface as 0.9.9)

## Next

No open **0.9.x** items. Further work needs a new drafted series in [Priority](/project/priority). Held items below stay held.

### Closed — 0.9.x ergonomics / OOP polish

Series complete through **0.9.9**; stable cut is **1.0.0**. Not inheritance, packages, or generics.

| Version | Item | Status |
| --- | --- | --- |
| 0.9.0 | Compound assign on members (`this.x += 1`) | implemented (0.9.0) |
| 0.9.1 | `priv` / field–method visibility | implemented (0.9.1) |
| 0.9.2 | Positional construction `Point(3, 4)` | implemented (0.9.2) |
| 0.9.3 | Deep `clone()` | implemented (0.9.3) |
| 0.9.4 | Named `format()` placeholders via trailing hash | implemented (0.9.4) |
| 0.9.5 | Class properties `get` / `set` | implemented (0.9.5) |
| 0.9.6 | `mkdirAll` / `removeTree` | implemented (0.9.6) |
| 0.9.7 | Regex builtins | implemented (0.9.7) |
| 0.9.8 | Union narrowing in `if type(...)` | implemented (0.9.8) |
| 0.9.9 | Thin dates builtins | implemented (0.9.9) |
| 1.0.0 | Stable release | implemented (1.0.0) |

Details: [Priority — 0.9.x](/project/priority).

## Held

Not near-term. Do not treat these as upcoming releases unless a draft series exists above:

- Generics, async, VM / JIT, packages
- `try` / `catch`, `Result` / `Option`, user-level recovery syntax
- Overloading, LSP
- HTTP builtins (dates shipped in **0.9.9**; regex in **0.9.7**; `mkdirAll` / `removeTree` in **0.9.6**)
- Test DSL (`test "name" { }`)
- Class inheritance (out of 0.8; interfaces only; not the 0.9 ergonomics spine)

See [Known Limitations](/errors-diagnostics/known-limitations) and [failure model](/failure-model).

## See Also

- [Priority](/project/priority)
- [Known Limitations](/errors-diagnostics/known-limitations)
- [CLI and Execution Model](/reference/cli-and-execution-model)
