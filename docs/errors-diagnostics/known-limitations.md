# Known Limitations

What Echo still does **not** do. As of **2.1.5**, the language includes modules (sibling + nested / relative paths, `std/…` install-tree imports through `std/re` / `std/time` / `std/yaml`, optional `--require-std` prelude policy, clearer cycle / not-found diagnostics), CLI tooling (`check` / `test` / `fmt` / `lint` / `builtins` / `lsp`), first-class functions, `const` / destructuring / unions / `switch`, nominal classes with `new { ... }` fields (including defaults), bound/unbound/type methods, optional `implements`, interfaces (no inheritance), compound assignment on members, `priv` visibility, positional construction, deep `clone()`, named `format` placeholders, class properties (`get` / `set`), recursive `mkdirAll` / `removeTree`, regex builtins (also `std/re`), union narrowing in `if type(...)`, thin UTC dates (also `std/time`), thin HTTP (also `std/http`), thin URL helpers (also `std/url`), Base64 helpers (also `std/base64`), YAML helpers (`yamlParse` / `yamlParseOr` / `yamlWrite`, also `std/yaml`, **E2855**), file/JSON/env helpers also via `std/fs` / `std/json` / `std/os`, `watch` location / abort dumps, abort `Stack:` dumps and `trace`, documented **E2801** / **E2850**–**E2855** and module **E3001**–**E3005** codes, playground host-policy docs plus playground `std/…` imports, a thin `elang lsp` stub wired into the editor extension (diagnostics, builtin hover, goto-def; task matchers remain as fallback), and a generated builtin inventory (`tools/sync_builtins.py`). **2.0** is path resolution + std modules — not a package registry. This page is the remainder — not a changelog.

## Already in (summary)

- Core syntax and file modules (`import` / `export`; nested / relative paths in **2.0.0**; `std/…` in **2.0.2**)
- Host/stdlib, REPL, `check` / `test` / `fmt` / `lint`
- 0.6–0.7: lambdas, collection helpers, `const`, destructuring, exact objects, unions, `switch`, range-as-value
- 0.8: `class` + `new { ... }`, methods + `this`, unbound/type methods, `interface`, optional `implements`
- 0.9.0: compound assignment on class fields (`this.x += 1`)
- 0.9.1: `priv` on fields and methods (class-private)
- 0.9.2: positional construction `Point(3, 4)` (named `Point { ... }` still works)
- 0.9.3: deep `clone()` for lists, hashes, and class instances
- 0.9.4: named `format()` placeholders via trailing hash
- 0.9.5: class properties `get` / `set` (soft keywords; field-style access)
- 0.9.6: `mkdirAll(path)` / `removeTree(path)` for recursive create/delete
- 0.9.7: `regexMatch` / `regexFind` / `regexReplace` / `regexSplit` (Python `re`)
- 0.9.8: union narrowing in `if type(x) == "..."` (and matching `else if`)
- 0.9.9: `formatTime` / `parseTime` (UTC) plus `days` / `hours` / `minutes`
- 1.0.0: stable release (same surface as 0.9.9)
- 1.1.0: `httpGet` / `httpPost` with `Host.allow_http`
- 1.1.1: request headers, `httpOk` / `httpRedirect`, `httpGetOr` / `httpPostOr`
- 1.1.2: `urlEncode` / `urlDecode` / `urlJoin` / `urlQuery`
- 1.1.3: `watch` source locations + `Watched:` dump on abort
- 1.1.4: error-message / code pass (**E2801**, **E2850**–**E2853** documented)
- 1.1.5: playground host-policy docs (CLI vs playground `Host`)
- 1.1.6: `tools/sync_builtins.py` + builtin inventory page
- 1.1.7: `base64Encode` / `base64Decode` (**E2854**)
- 1.1.8: `elang builtins` (+ `-V` / help epilog)
- 1.1.9: series close (README / examples / playground docs for full **1.1** surface)
- 2.0.0: relative / nested import paths (`"./math"`, `"lib/math"`, `"../shared"`)
- 2.0.1: clearer **E3001**–**E3003** diagnostics (looked-for path, import location, nested cycle labels)
- 2.0.2: `import … from "std/…"` from the Echo install tree (seed `std/meta`)
- 2.0.3: HTTP family via `std/http` (prelude names still work)
- 2.0.4: URL + Base64 via `std/url` / `std/base64` (prelude dual-path)
- 2.0.5: files / JSON / env via `std/fs` / `std/json` / `std/os` (prelude dual-path)
- 2.0.6: regex + dates via `std/re` / `std/time` (prelude dual-path)
- 2.0.7: optional `--require-std` / `Host.require_std` (core vs peeled prelude)
- 2.0.8: docs / examples / playground for multi-file + `std/…`
- 2.0.9: **2.0.x** series close (path resolution + std modules, not a package manager)
- 2.1.0: `yamlParse` / `yamlWrite` (**E2855**); `std/yaml`
- 2.1.1: `yamlParseOr` + failure-model / docs
- 2.1.2: `elang lsp` thin stdio stub (diagnostics + builtin hover)
- 2.1.3: LSP goto-def for local + imported symbols
- 2.1.4: editor LSP client (`elang lsp` via vscode-languageclient; task matchers remain)
- 2.1.5: abort `Stack:` dump + `trace` helper (no stepper)

Details: [Roadmap](/project/roadmap) and `CHANGELOG.md`.

## Current Limitations

- No class inheritance (`extends`); shared behavior is interfaces + composition
- No generics
- No exceptions such as `try/catch` — abort stays the default; recovery is inquiry and `*Or` twins ([failure model](/failure-model)). `echo test` may continue after `expect*` failures; that is runner-only, not in-language recovery
- No overloads
- Function scope is lexical; reassignment of outer variables still requires `use mut`
- Nested collections inside a frozen list/hash are not recursively frozen; a nested value reached through a different mutable name can still be mutated
- Open object type aliases accept extra fields; use `exact { ... }` to reject them
- `null` is not a type — use `str | void` when a binding may hold `null`. Full flow-sensitive typing beyond simple-name `if type(...)` guards is not implemented
- Hash runtime indexing only supports string keys
- `format()` has no width / precision / alignment specs
- Properties are not part of interfaces (`implements` still checks methods only)
- Interpolation tokenization is not fully strict
- No date object type / local-timezone calendars (UTC unix seconds + `formatTime` / `parseTime` only)
- HTTP is thin (no cookies/session client, no multipart); playground denies HTTP (`allow_http=False`)
- No full LSP-as-product (thin `elang lsp` + editor client ship in **2.1.2**–**2.1.4**; tasks/matchers remain)
- No full debugger / stepper (abort `Stack:` + `watch` + `trace` ship through **2.1.5**)
- No package registry yet (stdlib peels + optional `--require-std` shipped through **2.0.7**)

## Why this page exists

So docs do not oversell the language, and so shipped work is not mistaken for missing.

## Where next work is tracked

See [Failure model](/failure-model), [Roadmap](/project/roadmap), and [priority](/project/priority).
