# Roadmap

Public status page for what ships today. The ordered implementation plan lives under Internals → [Priority](/project/priority). This page is not a promise list.

## Shipped (do not re-list as “later”)

Already in the language or CLI:

- File modules: `import` / `export` (v0.3)
- REPL (`echo` with no file), `echo check`, `echo test`, `echo fmt`, `echo lint`, `echo builtins`
- Exact object types: `exact { ... }` (0.7.2)
- Number literals `.5` / scientific form; multiline strings
- `const` (including param `const` in 0.7.9), destructuring (hash `as` rename, hash rest), builtins as values, range-as-value, unions (`int | str`), `switch` through 0.7.9
- Nominal `class` + construction (0.8.0); methods + `this` (0.8.1); `interface` (0.8.2); explicit `new { ... }` fields (0.8.3); field defaults (0.8.4); unbound methods (0.8.5); type methods (0.8.6); optional `implements` (0.8.7); docs/README release pass (0.8.8); first PyPI package `echolang` (0.8.9)
- Compound assign on class members (`this.x += 1`) (0.9.0); `priv` fields/methods (0.9.1); positional construction `Point(3, 4)` (0.9.2); deep `clone()` (0.9.3); named `format` placeholders (0.9.4); class properties `get`/`set` (0.9.5); `mkdirAll` / `removeTree` (0.9.6); regex builtins (0.9.7); union narrowing in `if type(...)` (0.9.8); thin dates `formatTime` / `parseTime` / duration helpers (0.9.9)
- Stable release **1.0.0** (same surface as 0.9.9)
- **1.1.x** complete (**1.1.0–1.1.9**): HTTP + URL + Base64, watch/abort polish, error-code docs, playground host policy, builtin sync, `elang builtins`, series docs/examples

## Next

**1.1.x** is complete. **2.0.x** (modules beyond siblings + stdlib peel) and **2.1.x** (YAML + LSP stub + std maturity) are drafted in [Priority](/project/priority).

### Drafted — 2.0.x modules + stdlib peel

| Version | Item | Status |
| --- | --- | --- |
| 2.0.0 | Relative / nested import paths | drafted |
| 2.0.1 | Import cycle / resolver diagnostics polish | drafted |
| 2.0.2 | Stdlib search path: `import … from "std/…"` | drafted |
| 2.0.3 | Peel HTTP into `std/http` | drafted |
| 2.0.4 | Peel URL + Base64 | drafted |
| 2.0.5 | Peel files / JSON / env | drafted |
| 2.0.6 | Peel regex + dates | drafted |
| 2.0.7 | Prelude policy (core vs std) | drafted |
| 2.0.8 | Docs / examples / playground | drafted |
| 2.0.9 | Series close | drafted |

### Drafted — 2.1.x YAML + LSP stub

| Version | Item | Status |
| --- | --- | --- |
| 2.1.0 | YAML helpers | drafted |
| 2.1.1 | YAML `*Or` + docs | drafted |
| 2.1.2 | Thin LSP stub | drafted |
| 2.1.3 | LSP goto-def | drafted |
| 2.1.4 | Editor LSP client | drafted |
| 2.1.5 | Debugger polish beyond `watch` | drafted |
| 2.1.6 | Further std peel | drafted |
| 2.1.7 | CLI std inventory | drafted |
| 2.1.8 | Docs generator expansion | drafted |
| 2.1.9 | Series close | drafted |

Details: [Priority — 2.0.x / 2.1.x](/project/priority).

### Closed — 1.1.x HTTP + polish

| Version | Item | Status |
| --- | --- | --- |
| 1.1.0 | `httpGet` / `httpPost` + `allow_http` host flag | implemented (1.1.0) |
| 1.1.1 | HTTP headers / status helpers / `*Or` twins | implemented (1.1.1) |
| 1.1.2 | YAML or URL helpers (only if still tiny) | implemented (1.1.2 — URL only) |
| 1.1.3 | `watch` / abort diagnostics polish | implemented (1.1.3) |
| 1.1.4 | Error-message / code pass | implemented (1.1.4) |
| 1.1.5 | Docs generator or playground HTTP policy | implemented (1.1.5 — playground host policy) |
| 1.1.6 | Thin docs generator / builtin sync | implemented (1.1.6) |
| 1.1.7 | `base64Encode` / `base64Decode` | implemented (1.1.7) |
| 1.1.8 | CLI builtin inventory polish | implemented (1.1.8) |
| 1.1.9 | Series close (docs / examples) | implemented (1.1.9) |

Details: [Priority — 1.1.x](/project/priority).

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

- Generics, async, VM / JIT
- `try` / `catch`, `Result` / `Option`, user-level recovery syntax
- Overloading, full LSP-as-product, `Point.new`
- Package registry / lockfiles / `elang add` (path resolution + std modules are **2.0**; registry after **2.1**)
- Test DSL (`test "name" { }`)
- Class inheritance (out of 0.8; interfaces only)

**1.1.x** is closed above. **2.0.x** / **2.1.x** are drafted under Next — do not re-list those as held.

See [Known Limitations](/errors-diagnostics/known-limitations) and [failure model](/failure-model).

## See Also

- [Priority](/project/priority)
- [Known Limitations](/errors-diagnostics/known-limitations)
- [CLI and Execution Model](/reference/cli-and-execution-model)
