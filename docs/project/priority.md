# Echo remaining-feature priority

Current tagged version is **v0.8.5**. **0.8.6** (type methods) is implemented but not yet tagged. **0.7 polish is complete** through 0.7.9. **0.8 OOP spine is complete** (0.8.0–0.8.2). **0.8.3–0.8.9** is the OOP polish arc ending in the first **PyPI** release. Failure model stays abort + `*Or`.

The completed 0.5.x work was language basics: a few host/stdlib builtins plus two syntax extensions, then CLI/editor tooling. **0.5.9** is the last 0.5.x slice: `echo check [paths...]` with directory recursion (same as `fmt` / `lint` / `test`) plus editor **Check workspace**. **0.5.8** adds a small `echo lint` rule batch (`test-naming`, `self-assign`, `unreachable-after-fail`). **0.5.7** wires `echo check` / `fmt` / `lint` / `test` into the VS Code/Cursor extension as tasks and Problems matchers (not an LSP). **0.5.6** ships the native `echo test` product (`expect*` helpers, file/function units, summary). **0.5.5** ships `fail(message)` and `echo lint`. **0.5.4** ships `echo fmt`. **0.5.3** ships `readFileOr`, `parseJsonOr`, `asIntOr`, and `asFloatOr`. **0.5.2** makes the REPL keep session state across submissions. **0.5.1** hardened the 0.5.0 CLI (REPL continuation/quit, `echo test` semantics) and playground `allow_run` host enforcement.

Status values: `pending` / `in progress` / `implemented (version)` / `held`.

## Implement now (0.5.x — completed)

| # | Item | Status |
| --- | --- | --- |
| 1 | `assert(cond, message)` | implemented (0.5.0) |
| 2 | `copyFile(src, dest)` + `pathJoin(...)` | implemented (0.5.0) |
| 3 | `run(command, args)` | implemented (0.5.0) |
| 4 | `now()` — unix time as `int` seconds | implemented (0.5.0) |
| 5 | `random()` / `randomInt(min, max)` | implemented (0.5.0) |
| 6 | Multiline strings `"""` / `'''` | implemented (0.5.0) |
| 7 | Number literals `.5` and `1e3` / `1e-3` | implemented (0.5.0) |
| 8 | `readLine()` | implemented (0.5.0) |
| 9 | REPL (`echo` with no file) | implemented (0.5.2) |
| 10 | `echo test` product | implemented (0.5.6) |
| 11 | `fail(message)` | implemented (0.5.5) |
| 12 | `echo lint` | implemented (0.5.5), expanded (0.5.8) |
| 13 | `expect` / `expectEq` / `expectNeq` | implemented (0.5.6) |
| 14 | Editor tasks + problem matchers | implemented (0.5.7), Check workspace (0.5.9) |
| 15 | `echo check [paths...]` | implemented (0.5.9) |

### 1. `assert(cond, message)`

Abort with an Echo error if `cond` is falsy. `message` must be `str`. No Python `AssertionError` leaks. Analyzer: min 2 standalone args.

### 2. `copyFile` + `pathJoin`

`copyFile(src, dest)` is a UTF-8-agnostic binary copy of a file (not a directory). Restricted host (`allow_files=False`) denies with E2801. Missing src aborts. Missing dest parent aborts. Overwriting dest overwrites the file; abort if dest is a directory.

`pathJoin` takes 2+ string parts (variadic like `say`). Uses pathlib join, not string concat. Restricted host: `pathJoin` stays available (pure path strings; no files).

### 3. `run(command, args)`

`command` is `str`. `args` is a list of `str` (empty list allowed). Returns `{ "code": int, "stdout": str, "stderr": str }`. No `shell=True`. `Host.allow_run: bool = True` by default; playground sets `allow_run=False`. Denied run → E2801-style “not available in this host”. Non-zero exit is not an Echo error. Missing executable is an Echo error.

### 4. `now()`

No arguments. Returns unix time as `int` seconds.

### 5. `random` / `randomInt`

`random()` → float in `[0, 1)`. `randomInt(min, max)` inclusive integers, reject `bool`, require `min <= max`. Python `random`.

### 6. Multiline strings

Triple-quote `"""` and `'''`. Interpolation `${...}` works, matching `"..."` / `'...'`. Newlines are allowed only in triples; single-line quotes stay single-line.

### 7. Number literals

`.5` and scientific `1e3` / `1e-3`. Keep existing `5.` as integer then `.` (method calls like `5.asInt()` stay valid).

### 8. `readLine()`

Read one line from stdin with no required prompt. EOF aborts with an Echo error.

### 9. REPL

`echo` with no file enters a REPL. Keep `echo check` and `echo file.echo`. `--plain` supported.

Harden 0.5.1: brace-depth and unterminated-triple continuation (`... `), empty lines ignored, `exit(code)` / EOF quit without a traceback, one failed submission does not kill the process.

**0.5.2 REPL session state (done):** one Interpreter and Environment for the process. Analyzer-visible declarations persist across successful submissions, so a `fn` or variable defined at one `echo>` is usable at the next. Failed submissions do not drop earlier bindings. `import` loads sibling modules from the working directory into the session. `use mut` works for names declared earlier in the session.

### 10. `echo test`

`echo test [paths...]` is the native runner (0.5.6). No test DSL. No `test "name" { }` keyword.

A directory argument recursively runs `*_test.echo` files. An explicit file path always runs. No path prints help and exits 2. The first argv token `test` is the subcommand; `echo test.echo` still runs that file.

Zero-argument top-level `fn testXxx()` functions are separate units. Remaining top-level statements run once as setup, or as the file unit when there are no such functions. Exit 0 if every unit passed; 1 if any failed.

Harden 0.5.1: no path → help and exit 2; missing file → non-zero Echo error; `exit(2)` fails the unit; `exit(0)` passes; imported modules execute (unlike `check`).

### 11. `fail(message)`

Abort with an Echo error. `message` must be `str`. Same diagnostic family as `assert` (code **E2825**). Always abort. No `*Or` twin. Required message so scripts stay explicit.

### 12. `echo lint`

Style and convention findings, not a second typechecker. `echo lint [paths...]` walks files or recursive `*.echo` directories. Findings exit 1; clean exit 0; no path prints help and exits 2; parse errors match `echo check`. The first token `lint` is the subcommand; `echo lint.echo` still runs that file.

Rules: `unused-local`, `unused-function`, `unused-import`, `comparison-to-bool`, `redundant-by-one`, `empty-block`, `shadow-builtin`, `test-naming`, `self-assign`, `unreachable-after-fail`. Zero-arg `fn test*` entries are not unused-function (the test runner calls them). `test-naming` flags a top-level `fn` that looks like a test (`test*` / `Test*`) but is not a zero-arg `testXxx` unit. Unused parameters stay `unused-local`. `unused-export` is skipped (exports are for importers; no file-local convention). `redundant-parens` is skipped (the AST does not keep grouping parentheses).

### 13. `expect` / `expectEq` / `expectNeq`

Test-only continue-after-failure helpers. `message` must be `str`. `expect(cond, message)` requires `cond` to be `bool`. Under `echo test` a false/mismatch **records** and the unit continues. Outside `echo test` they abort like `assert`. `assert` / `fail` still abort. Codes **E2826** / **E2827** / **E2828**.

### 14. Editor tasks + problem matchers

VS Code / Cursor integration in `echo-syntax-highlighter/`: Run Task / command palette for `echo check`, `echo fmt`, `echo lint`, and `echo test`, with problem matchers into the Problems panel. Tasks use `--plain`. **Echo: Check workspace** (0.5.9) runs `echolang check --plain` on the folder; **Echo: Check file** remains. Not an LSP: no completions, jump-to-definition, or language-server diagnostics.

### 15. `echo check [paths...]`

Last 0.5.x tooling slice. No new language syntax.

`echo check [paths...]` walks files or recursive `*.echo` directories, same collection helper as `fmt` / `lint`. Analyze only; do not run. Exit 0 if every file is clean; 1 if any parse/semantic check fails. After a failure, continue so `echo check .` reports every bad file, then exit 1. Missing path exits 1. No path prints help and exits 2. The first token `check` is the subcommand; `echo check.echo` still runs that file. `--plain` is supported.

## 0.6.x

**0.5.9** closed the 0.5.x tooling arc. **0.6** opened language (functions as values, then collection helpers on those values). Current tag is **v0.8.5**. **0.6.x is complete.** **0.7.0**–**0.7.9** are implemented. **0.8.0–0.8.5** are implemented; **0.8.6** is implemented (not yet tagged); polish **0.8.7–0.8.9** remains drafted.

**0.6.0** shipped all three language items in **one** release:

1. First-class functions **including lambdas**
2. Slice syntax
3. Default **and** variadic user `fn` args **together**

**0.6.1** ships list `map` / `filter` on the function values from 0.6.0.

**0.6.2** ships list `reduce` on those same function values.

**0.6.3** ships list `forEach` on those same function values.

**0.6.4** ships list `flatMap` on those same function values.

**0.6.5** ships list `some` / `every` / `findIndex` on those same function values.

**0.6.6** ships optional slice bounds `xs[1:]` / `xs[:4]` / `xs[:]` on the slice syntax from 0.6.0.

**0.6.7** ships list `zip` / `unique`. (`unique` was originally queued as 0.6.8.)

**0.6.8** ships four items: `echo test -run`, list `chunk`, `rangeList` / `rangeListInclusive`, and hash `mapValues` / `filter`.

**0.6.9** ships four items: function types honor trailing defaults, list `flatten`, list `partition`, and `echo test --json`. Last 0.6.x slice.

Failure model is unchanged through 0.6.9: callbacks or default expressions that abort still abort. No `try` / `catch`. No `Result` / `Option`. No extra `*Or` twins in this stretch — the 0.5.3 set still covers the designed recovery cases.

Already shipped, so **not** re-proposed: `args` / `env` / files / JSON / `fmt` / `lint` / `test` / `check` / `map` / `filter` / `reduce` / `forEach` / `flatMap` / `some` / `every` / `findIndex` / `zip` / `unique` / `chunk` / `rangeList` / `mapValues` / hash `filter` / `echo test -run` / `echo test --json` / `flatten` / `partition` / function-type trailing defaults / `slice()` / `xs[1:4]` / optional slice bounds / lambdas / defaults / variadics / `order(comparator)` / `find(value)` / `reverse` / `contains`.

Held items below stay held through 0.7 (VM/JIT, classes, generics, async, packages, try/catch, Result/Option, overloading, LSP, dates/HTTP/regex, `mkdir -p`, test DSL). `const` / destructuring / exact objects / builtins-as-values / range-as-value are the **0.7** spine, not leftovers.

| Version | Item | Status |
| --- | --- | --- |
| 0.6.0 | First-class functions including lambdas | implemented (0.6.0) |
| 0.6.0 | Slice syntax `xs[1:4]` | implemented (0.6.0) |
| 0.6.0 | Default and variadic user `fn` args | implemented (0.6.0) |
| 0.6.1 | `map` / `filter` | implemented (0.6.1) |
| 0.6.2 | `reduce` | implemented (0.6.2) |
| 0.6.3 | `forEach` | implemented (0.6.3) |
| 0.6.4 | `flatMap` | implemented (0.6.4) |
| 0.6.5 | `some` / `every` / `findIndex` | implemented (0.6.5) |
| 0.6.6 | Optional slice bounds `xs[1:]` `xs[:4]` `xs[:]` | implemented (0.6.6) |
| 0.6.7 | `zip` / `unique` | implemented (0.6.7) |
| 0.6.8 | `echo test -run` | implemented (0.6.8) |
| 0.6.8 | `chunk` | implemented (0.6.8) |
| 0.6.8 | `rangeList` / `rangeListInclusive` | implemented (0.6.8) |
| 0.6.8 | hash `mapValues` / `filter` | implemented (0.6.8) |
| 0.6.9 | Function types honor defaults | implemented (0.6.9) |
| 0.6.9 | `flatten` | implemented (0.6.9) |
| 0.6.9 | `partition` | implemented (0.6.9) |
| 0.6.9 | `echo test --json` | implemented (0.6.9) |

### 0.6.0 — first-class functions (including lambdas)

Functions are values. Lambda spelling: **`fn(x: int) -> int { ... }`** (inline `=>` also works). Function type spelling: **`fn(int) -> int`**. `order(comparator)` accepts a function value, a lambda, or a name string.

### 0.6.0 — slice syntax

Spelling: **`xs[1:4]`** (colon, not `..`). 0.6.0 required both bounds. **0.6.6** allows omitting either or both (`xs[1:]`, `xs[:4]`, `xs[:]`). Desugars to existing `slice(start, end)` with the same bounds as today: start and end in `[0, length]`, end exclusive, no negatives, out-of-bounds aborts.

### 0.6.0 — default and variadic user `fn` args

User `fn` default arguments and variadic arguments ship **together**. Spelling: **`punct: str = "!"`** and **`parts: int...`** (variadic last, rest is a `list` of `T`). Defaults come before the variadic and are evaluated at call time. Overloading stays held. Function types still spell parameter types only (`fn(int, str) -> int`). **0.6.9** treats defaulted trailing parameters as optional when assigning.

### 0.6.1 — `map` / `filter`

List `map(items, f)` / `filter(items, f)` and method form `items.map(f)` / `items.filter(f)`. `filter` requires a `bool` return (`1` is not kept). Callbacks that abort abort the call. No string variants. Hash `mapValues` / `filter` ship in **0.6.8**.

### 0.6.2 — `reduce`

List `reduce(items, init, f)` / `items.reduce(init, f)`. `f` is `fn(acc, item) -> acc`. `init` is required; empty list returns `init` and does not call `f`. Returns a new value; does not mutate the input. A callback that aborts aborts the call. List only. No second `fold` builtin. Codes: non-function `f` **E2832**, wrong arity **E2833**, callback result type ≠ `init` **E2834**.

### 0.6.3 — `forEach`

List `forEach(items, f)` / `items.forEach(f)`. Unary callback; the return value is discarded. Returns `null`. Does not mutate the input itself (the callback may, under `use mut`). Empty list is a no-op. A callback that aborts aborts the call. List only.

### 0.6.4 — `flatMap`

List `flatMap(items, f)` / `items.flatMap(f)`. Unary `f` must return a `list`; a non-list return is a type error. Concatenates those lists **one** level into a new list. Empty input returns `[]`. Does not mutate the input. A callback that aborts aborts the call. List only. Codes: non-function `f` **E2837**, wrong arity **E2838**, callback result not a list **E2839**.

### 0.6.5 — `some` / `every` / `findIndex`

List predicates on a unary `fn(T) -> bool` (same bool rule as `filter`). `some` is `true` if any element matches (empty → `false`). `every` is `true` if all match (empty → `true`). `findIndex` is the first matching index, or `-1` if none — same sentinel as existing `find(value)`. `find(value)` stays value search; do not overload it. Short-circuit. Method + standalone. List only. Callbacks that abort abort the call. Codes: non-function `f` **E2840**, wrong arity **E2841**, non-`bool` callback result **E2831** (same as `filter`).

### 0.6.6 — optional slice bounds

`xs[1:]`, `xs[:4]`, and `xs[:]` parse and desugar to `slice`. Omitted start is `0`; omitted end is `length`. Same abort rules as today for any bound that is present: `[0, length]`, end exclusive, no negatives, out of range aborts. `xs[:]` is `slice(0, length)`. Lists and strings, matching `slice()`. This is why 0.6.x does not also ship `take` / `drop`.

### 0.6.7 — `zip` / `unique`

Standalone `zip(left, right)` (and `left.zip(right)`) → a new list of 2-element lists `[left[i], right[i]]`. Both arguments must be `list`. Length is `min(len(left), len(right))` (unequal is not an Echo error). Empty either side returns `[]`. Does not mutate the inputs. Two lists only — no N-way zip, no zipper callback (that is `map` after `zip`, or later). Keywords `left:` / `right:`.

List `unique(items)` / `items.unique()` → a new list of first occurrences in original order, using Echo `==`. Does not mutate the input. Empty → `[]`. List only. Not `reverse` (already in-place on lists). Not hash `take`. Keyword `items:`.

### 0.6.8 — `echo test -run`, `chunk`, `rangeList`, hash `mapValues` / `filter`

Four items in one release. No new keywords. Failure model is unchanged.

`echo test -run PATTERN` (also `--run`) is a Go-shaped glob filter on **function unit names** (`testXxx`), not file names. `*Add*` matches `testAdd`; `testAdd` is exact. Non-matching units are skipped, not failed. A file with no matching units is skipped (not failed). Directories / `*_test.echo` still apply. `--plain` is unchanged. `echo test.echo` still runs that file.

`chunk(items, size)` / `items.chunk(size)` splits a list into new sublists of length `size` (`int` `>= 1`); the last chunk may be shorter. Empty list is `[]`. Does not mutate the input.

`rangeList(start, end)` is exclusive-end, matching `for i in start...end` (step `1`). `rangeListInclusive(start, end)` matches `start..end`. Empty when that `for` would not iterate. Returns `list` of `int`. Not `0...10` as a list value.

`mapValues(h, f)` / `h.mapValues(f)` returns a new hash with the same keys. Unary `f(value) -> newValue`. `filter` on a hash uses the same name as list `filter` and dispatches on the first argument / receiver type. `f(value)` must return **bool** `true` (not `1`). Empty hash is empty hash. Insertion order is preserved. Callback abort still aborts. Does not mutate the input.

### 0.6.9 — function types honor defaults, `flatten`, `partition`, `echo test --json`

Four items in one release. Last 0.6.x slice. No new keywords. Failure model is unchanged.

Closes the 0.6.0 caveat: types still spell **`fn(int) -> int`** (no default markers, no `?`). A function whose trailing parameters have defaults is assignable to a function type that **omits** those parameters, and still to the full-arity type. `fn(x: int, y: int = 0) -> int` matches `fn(int) -> int` and `fn(int, int) -> int`, not `fn() -> int`. Calls through the narrower type pass only those args; the implementation fills defaults at call time. Required parameters and variadics still have to match the type. Not builtins-as-values.

`flatten(items)` / `items.flatten()` concatenates **one** level of nested lists into a new list. Empty → `[]`. A top-level non-list element is a type error. Does not mutate the input. Keyword `items:`.

`partition(items, f)` / `items.partition(f)` returns `[matches, rest]`. Unary `f: fn(T) -> bool` (same bool rule as `filter`: `1` is not ok). Empty → `[[], []]`. Callback abort still aborts. Does not mutate the input. Keywords `items:` / `f:`.

`echo test --json` writes a machine-readable JSON report to stdout. Totals include passed / failed / skipped (from `-run`). Each unit has name, pass/fail, and failure message + location when present. Composes with `-run` / `--run` and `--plain`. Human summary is off. Exit codes stay 0 / 1 / 2. `echo test.echo` still runs that file.

## 0.7.x

**0.6.x is complete.** **0.7 is the big-gun language series.** Policy: one language-scale increment per version — syntax, type system, or value-model. Not `chunk` / `zip`-sized stdlib. Not another higher-order-function drip.

Spine (reserved for 0.7, not late 0.6): `const`, destructuring, exact object types, builtins as values, range as a value. Two more language items fit the same series: union types, then `switch` on values. String `map` / `filter` over graphemes stays skipped.

Failure model is unchanged through 0.7: abort by default; recovery is inquiry and the 0.5.3 `*Or` twins. No `try` / `catch`. No `Result` / `Option`. No `?`. `switch` is value dispatch, not error handling ([failure model](/failure-model)).

Already shipped, so **not** re-proposed: everything in 0.5.x and 0.6.x (including `rangeList` / `rangeListInclusive`, function values for **user** `fn` / lambdas, open object aliases).

Held items below stay held through 0.7. Do not pull VM/JIT, classes, generics, async, packages, overloading, LSP, dates/HTTP/regex, `mkdir -p`, or a test DSL into this series.

Working spellings below are the plan of record so each version can be implemented without a second design pass. Open questions at the end of this section are the only knobs; changing one does not reorder the series.

| Version | Item | Status |
| --- | --- | --- |
| 0.7.0 | `const` bindings | implemented (0.7.0) |
| 0.7.1 | Destructuring | implemented (0.7.1) |
| 0.7.2 | Exact object types | implemented (0.7.2) |
| 0.7.3 | Builtins as values | implemented (0.7.3) |
| 0.7.4 | Range as a value | implemented (0.7.4) |
| 0.7.5 | Union types | implemented (0.7.5) |
| 0.7.6 | `switch` on values | implemented (0.7.6) |
| 0.7.7 | Hash destructure rename | implemented (0.7.7) |
| 0.7.8 | Hash destructure rest | implemented (0.7.8) |
| 0.7.9 | Param `const` | implemented (0.7.9) |

### 0.7.0 — `const` bindings

Declaration-site immutability. Completes Echo's mutability story: `use` / `use mut` are capture; imports are Model A; **`const` is the declaring-scope form**.

**Implemented spelling:** **`const name: T = expr;`**. `export const name: T = expr;` is allowed. Types stay required (same as ordinary `name: T =`). The binding must be initialized. Reassignment of that name is a semantic error (**E3201**). `use mut name;` of a `const` binding is a semantic error (**E3204**). In-place collection mutation through that name (`push`, `xs[i] = v`, and other mutating methods) is rejected (**E3202**) — aligned with `use`, not JavaScript `const`.

The bound list or hash is **frozen**. Mutating that value through another name or a function parameter aborts (**E3203**). Reading / iterating / `map` (new list) is fine. Nested collections reached through a *different* mutable name are not deep-frozen. **0.7.9** adds `const` on parameters (`fn f(const xs: list)`).

Does not add a new runtime type. Ordinary (non-const) imported collections keep Model A identity. `watch` on a `const` name is legal and will simply never fire from that binding.

### 0.7.1 — destructuring

Unpack lists and hashes into names in one binding. This is new declaration / assignment syntax, not a stdlib helper.

**Implemented spelling:** **`[a: int, b: int] = pair;`** and **`{ id: int, name: str } = user;`**. Types are required on a fresh declaration (Echo does not infer). Rest is last: **`[head: int, rest: int...] = xs`** binds `rest` as a `list` of `T`. Nested list patterns are allowed (`[[a: int], b: int]`). Compose with `const`: **`const [a: int, b: int] = pair;`**. Reassignment to already-declared names omits types: **`[a, b] = pair;`**. Same patterns in function parameters: **`fn f([a: int, b: int]) { }`** (the parameter type is `list` or `hash`).

Hash patterns bind listed keys; missing keys abort (**E2711**, same as `user["x"]`). Extra keys are ignored unless the source is an exact object type (0.7.2). Length mismatch on a list pattern without rest aborts (**E3205**). Wrong container type is **E3206** / **E3207**. A callback or initializer that aborts still aborts.

Default: the field name is the binding name. **0.7.7** adds rename: **`{ id as userId: int }`**. **0.7.8** adds hash rest: **`{ id: int, rest: dynamic... }`**.

### 0.7.2 — exact object types

Closed hash shapes. Today `type User = { id: int, name: str }` requires those fields and **allows extras**. Exact types reject extras. This is the type-system counterpart of hashes-as-records, not structs or classes.

Implemented spelling: **`exact { id: int, name: str }`** as a type constructor, in aliases and inline (`fn f(user: exact { id: int })`). Open `{ id: int, name: str }` stays open — **not a breaking change**. Aliases remain names, not nominal runtime types. Exact types require every listed key and type and reject extras at declarations, assignments, arguments, returns, destructured bindings, and `foreach` bindings. Exact → compatible open is assignable; open → exact is not. Extra fields are **E3208** and missing fields are **E3209**. Exactness nests and does not freeze the hash.

Does not add methods on aliases. Does not add classes. `dynamic` still accepts any hash.

### 0.7.3 — builtins as values

Closes the 0.6 function-value hole. Named **user** functions are already values; **`say` / `map` / `filter` and the other standalone builtins** are assignable, passable, returnable function values with `fn(...)` types.

**Implemented:** `f: fn(list, fn(dynamic) -> dynamic) -> list = map;` is legal, as is `fn(list, fn(int) -> int) -> list = map` when the callback slot is the wide builtin type. Calls through that value are ordinary calls. Variadic builtins (`say`, `eprint`, `format`, `pathJoin`) are typed `fn(dynamic...) -> void` (`say` / `eprint`) or `fn(dynamic...) -> str` (`format` / `pathJoin`) — Echo has no `null` type, so `void` is the return. Dispatch builtins (`filter` on list vs hash) keep runtime dispatch on the first argument / receiver. Host-denied builtins remain values; **calling** them still aborts `E2801`. Method form without a call is also a value (`xs.map`); unknown properties still error **E2704**. Equality is the same builtin (interned name) or, for bound methods, the same builtin and the same receiver object. `const` bindings of a builtin alias cannot be reassigned; the builtin itself is not a mutable object.

Not overloading. Not a new `Callable` type. Function types still spell parameter types only (0.6.9 defaults rules unchanged).

### 0.7.4 — range as a value

`start...end` and `start..end` become expressions that produce a `list` of `int`, same bounds as `for` / `rangeList` / `rangeListInclusive`. **`0...10` is `[0, 1, ..., 9]`**; **`0..10` is `[0, 1, ..., 10]`**. Optional **`by step`** in expression position: `0...10 by 2`. Eager list; no `Range` type. Empty when that `for` would not iterate. Non-numeric bounds and `by 0` abort as they do in `for`.

`for i: int in 0...10` stays the dedicated numeric loop (does not allocate a list). `foreach i: int in 0...10` iterates the list value. Keep `rangeList` / `rangeListInclusive`; they are the same values as the exclusive / inclusive expressions. Slice syntax stays colon (`xs[1:4]`); `xs[0...10]` is indexing with a list and is a type error.

**Implemented** as above.

### 0.7.5 — union types

Runtime-checked unions as a typed alternative to `dynamic`. **Implemented spelling:** **`int | str`** in type position (`||` stays boolean or). Flatten duplicates (`int | str | int` is `int | str`). `int` is assignable to `int | str`; `int | str` is not assignable to `int`. Object types, function types, and `exact { ... }` may be members. Lists stay untyped sequences (`list`); a binding may be `list | hash`.

Echo has no `null` type (`null` is only a `dynamic` value), so `str | null` does not parse — use `str | void` when a binding may hold `null`. Unions are **not** `Option` / `Result`: no `?`, no unwrap, no error recovery. Control-flow narrowing (`if type(x) == "int"`) is **not** implemented in 0.7.5.

Does not add generics, tagged enums, or exhaustiveness at compile time. Exhaustiveness belongs to `switch` (0.7.6) as a runtime/analyzer check on finite unions, not a new type-theory layer.

### 0.7.6 — `switch` on values

Value dispatch. This is control flow for literals, unions, and destructuring patterns — **not** error handling. Keyword is **`switch`**, not `match`, so `match` stays associated with the held `Result` / `Option` revision.

**Implemented spelling** (statement form; Echo is statement-based):

```echo
switch x {
    0 { say("zero"); }
    1 { say("one"); }
    else { say("other"); }
}
```

Arms: literal equality, type patterns (`int { }` / `int n { }`), and 0.7.1 destructuring patterns. `else` is required unless the arms cover a typed `bool` (`true` and `false`) or every member of a typed union via type patterns (**E3210**). A failed pattern does not abort the `switch`; it tries the next arm. No `try`. Aborting inside an arm still aborts. No expression-form `switch` in 0.7.6.

### 0.7.7 — hash destructure rename

Bind a hash key to a different local name. Completes a 0.7.1 open question; does not add hash rest.

**Implemented spelling:** **`{ id as userId: int }`**. Key is `id`; binding is `userId`. Same-name stays `{ id: int }`. Assignment omits types: **`{ id as userId } = user;`**. Works in declarations, assignment, function parameters, and `switch` hash arms. Keyword **`as`**. `{ id: int as userId }` is **not** the spelling.

### 0.7.8 — hash destructure rest

Collect leftover keys into a hash binding. Completes the other 0.7.1 open gap beside rename.

**Implemented spelling:** **`{ id: int, rest: dynamic... }`**. Fixed fields bind as usual; remaining keys bind as a **`hash`** named `rest`. `T...` is the value type for each leftover entry; the binding’s type is always `hash`. Rest must be last. No `as` on the rest field. Assignment: **`{ id, rest... } = user;`**. Empty leftovers are `{}`. Compose with rename: `{ id as userId: int, rest: dynamic... }`.

### 0.7.9 — param `const`

Declaration-site immutability for parameters. Same rules as binding `const`.

**Implemented spelling:** **`fn f(const xs: list) { ... }`**, including lambdas, defaults, variadics (`const xs: int...`), and destructuring params (`const [a: int, b: int]`). Reassignment is **E3201**. In-place mutation through that name is **E3202**. `use mut` on a const param is **E3204**. The bound list/hash is frozen (shared identity with the argument).

### 0.7 open questions

These are spelling / tightness knobs. They do not add versions and they do not reopen Held.

| Topic | Working assumption | Alternatives |
| --- | --- | --- |
| `const` keyword | `const name: T = expr;` (locked in 0.7.0) | type-side `name: const T = expr;` |
| `const` vs mutation | no reassignment **and** freeze of the bound list/hash (locked in 0.7.0); nested values via another name are not deep-frozen; param `const` locked in 0.7.9 | reassignment-only (JS-like); recursive deep freeze |
| Destructure types | types on fresh names; omitted on reassignment | always repeat types |
| Hash rename | `{ id as userId: int }` (locked in 0.7.7) | `{ id: int as userId }` |
| List rest | `[head: int, rest: int...]` | a `..rest` token |
| Hash rest | `{ id: int, rest: dynamic... }` (locked in 0.7.8); binding is `hash`; `T...` is value type; no `as` on rest | require `hash...` token; allow rename on rest |
| Exact objects | opt-in `exact { ... }`; open `{ ... }` unchanged | `#{ ... }`; `{ ... }!`; closed-by-default + `...` rest (breaking) |
| Builtin function types | real `fn(...)` types, including variadics | `dynamic` callable with no signature |
| Range `by` | `0...10 by 2` as an expression | step only in `for`; value form always step `1` |
| Union bar | `int \| str` (locked in 0.7.5) | a `or` type keyword |
| `str \| null` | forbidden — no `null` type; use `str \| void` for nullability (locked in 0.7.5) | invent a `null` type member |
| Switch keyword | `switch` | `match` (rejected: failure-model collision) |
| Switch narrowing | arm `int { }` / `int n { }` on a union | literals + `else` only |

## 0.8.x — OOP

**Status: spine 0.8.0–0.8.2 implemented; polish 0.8.3–0.8.6 implemented; 0.8.7–0.8.9 drafted (held until started).**

**0.7 is closed** (spine through 0.7.6; polish through 0.7.9). Records stay hashes + `exact { ... }` + aliases. **0.8 adds nominal types with behavior** — not “methods on type aliases,” and not classical Java (no inheritance-first design).

Shape: **structs with methods**, Echo-flavored.

- Nominal `class` names (runtime identity, not structural)
- Fields are an **exact** shape (extras rejected)
- Methods use the existing call form `obj.method(args)` (same surface as list/hash builtins) — **0.8.1**
- Interfaces are capability types (method signatures) — **0.8.2**
- Failure model unchanged: abort + `*Or`; no exceptions from methods
- Open `{ ... }` hashes and `exact { ... }` keep working; classes do not replace them
- Generics, overloading, async, packages, VM stay held outside this spine
- **Public release:** first PyPI upload of `echolang` at **0.8.9** (not earlier)

### Spine (done)

| Version | Item | Status |
| --- | --- | --- |
| 0.8.0 | Nominal `class` + construction | implemented (0.8.0) |
| 0.8.1 | Methods + `this` | implemented (0.8.1) |
| 0.8.2 | `interface` (no inheritance) | implemented (0.8.2) |

### Polish (draft / held until started)

Do not implement until explicitly started (`start 0.8.3`, etc.). Goal: make the OOP surface teachable and release-ready, then publish.

| Version | Item | Status |
| --- | --- | --- |
| 0.8.3 | Explicit `new { ... }` field block | implemented (0.8.3) |
| 0.8.4 | Field defaults in `new` / construction | implemented (0.8.4) |
| 0.8.5 | Unbound methods `Point.length(p)` | implemented (0.8.5) |
| 0.8.6 | Type methods (no `this`) / `Point.origin()` | implemented (0.8.6) |
| 0.8.7 | Optional `implements` clause | held (draft) |
| 0.8.8 | Docs / examples / README release pass | held (draft) |
| 0.8.9 | First PyPI release (`echolang`) | held (draft) |

### 0.8.0 — nominal `class` + construction

Introduce a nominal type distinct from `type Alias = exact { ... }`.

**Implemented spelling** (field block later moved under `new { ... }` in **0.8.3**):

```echo
class Point {
    new {
        x: int;
        y: int;
    }
}

p: Point = Point { x: 3, y: 4 };
say(p.x);
p.x = 10;
```

Rules:

- `class Name { new { field: T; ... } }` declares a nominal type `Name` (as of 0.8.3)
- Field list is **exact**: every field required; extras abort (**E3208** / **E3209**)
- Construct with **`Name { field: expr, ... }`** (named fields only; order free). No positional `Point(3, 4)` in 0.8.0
- `export class Name { ... }` allowed, same as other top-level declarations
- Nested classes: **no** in 0.8.0 (top-level only)
- Empty field list allowed (`class Marker { }`) for nominal tags
- `type(p)` returns the class name string (e.g. `"Point"`), not `"hash"`
- Assignability: `Point` is only assignable to `Point` (and `dynamic`). A compatible `exact { x: int, y: int }` hash is **not** a `Point`. `Point` is not assignable to that exact type either — nominal, not structural
- `Point` may appear in unions (`Point | str`) and in `switch` type arms (`Point { }` / `Point p { }`)
- Field read/write: `p.x` and `p.x = v` (typed). Unknown field → **E2704**
- `const p: Point = ...` freezes the instance (**E3202** through that name; **E3203** via another name)
- Destructuring: `{ x: int, y: int } = p` works (instances are hash-shaped for destructure)
- Equality: field-wise Echo `==` (like hashes), not identity
- No methods, no `this`, no inheritance, no `private` in 0.8.0

Does not add a separate `struct` keyword. `class` is the keyword; behavior is struct-like.

### 0.8.1 — methods + `this`

Attach functions to a class. Receiver is explicit as the first parameter named **`this`**.

**Implemented spelling:**

```echo
class Point {
    new {
        x: int;
        y: int;
    }

    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }

    fn move(this, dx: int, dy: int) -> void {
        this.x = this.x + dx;
        this.y = this.y + dy;
    }
}

p: Point = Point { x: 3, y: 4 };
say(p.length());
p.move(1, 1);
bound: fn() -> int = p.length;
say(bound());
```

Rules:

- Methods are declared inside the class body as `fn name(this, ...) -> T { ... }` (or `=>` inline)
- First parameter **must** be named `this` and has type `Name` implicitly (do not write `this: Point`)
- Call form: `p.length()` — `this` is bound to `p`. Same surface as `xs.map(f)`
- Method as value: `p.length` is a bound `fn` (0.7.3 style). Standalone `Point.length` as an unbound function is **not** required in 0.8.1
- Methods may read/write fields through `this`
- No static methods in 0.8.1 (`Point.origin()` held)
- No method overloading (held globally)
- Abort inside a method aborts the caller
- Analyzer: unknown method → member error; wrong arity → existing call errors

### 0.8.2 — `interface` (no class inheritance)

Capability types without single-parent inheritance.

**Implemented spelling:**

```echo
interface Named {
    fn name(this) -> str;
}

class User {
    new {
        id: int;
        label: str;
    }

    fn name(this) -> str {
        return this.label;
    }
}

fn show(n: Named) {
    say(n.name());
}

u: User = User { id: 1, label: "Ada" };
show(u);
```

Rules:

- `interface Name { fn method(this, ...) -> T; ... }` — method signatures only, no fields in 0.8.2
- A class **implements** an interface by defining every method with a compatible signature (structural match on the class’s methods). No `implements` clause required in 0.8.2 (inferred)
- Assignability: class instance assignable to interface if it provides the methods. Interface to interface if the target’s methods are a subset
- `switch` on interfaces: not exhaustive by class list; `else` still required unless other finite rules apply
- **No** `extends` / class inheritance in 0.8. Shared behavior = interfaces + composition (store another instance as a field)
- No default method bodies in 0.8.2

### 0.8.3 — explicit `new { ... }` field block

Make the constructor surface obvious inside `class`, without changing the call site.

**Implemented spelling:**

```echo
class Point {
    new {
        x: int;
        y: int;
    }

    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }
}

p: Point = Point { x: 3, y: 4 };
```

Rules:

- Fields live under **`new { field: T; ... }`** (exact shape, same **E3208** / **E3209** rules)
- Call site stays **`Point { x: 3, y: 4 }`** (named fields only; order free)
- Methods stay top-level in the class body (`fn …(this, …)`); may appear before or after `new`
- Empty classes may omit `new` (`class Marker { }`) or use `new { }`
- Bare top-level `x: int;` inside `class` is a **parse error**
- At most one `new` block per class
- Keyword is **`new`**, not `construct` / `init`

Does not add ctor method bodies, positional `Point(3, 4)`, or `new Point(...)`.

### 0.8.4 — field defaults

Defaults on constructor fields so callers may omit them.

**Implemented spelling:**

```echo
class Point {
    new {
        x: int = 0;
        y: int = 0;
    }
}

origin: Point = Point {};
p: Point = Point { x: 3 };
```

Rules:

- Default is an expression evaluated at construction time (same evaluation rules as fn defaults)
- Omitted fields use their default; required fields without defaults still **E3209**
- Extra fields still **E3208**
- Construction field values (provided or defaulted) are type-checked (**E2001**)
- Defaults do not change assignability of `Point` itself

Does not add optional types or `null`-default sugar beyond what expressions already allow.

### 0.8.5 — unbound methods

Use a method without an instance binding, by passing the receiver explicitly.

**Implemented spelling:**

```echo
class Point {
    new { x: int; y: int; }
    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }
}

p: Point = Point { x: 3, y: 4 };
say(Point.length(p));
raw: fn(Point) -> int = Point.length;
say(raw(p));
```

Rules:

- `Point.length` is an unbound `fn(Point, …) -> T` (first param is the class type)
- `Point.length(p, …)` is equivalent to `p.length(…)` when `p` is `Point`
- Bound form `p.length` stays as in 0.8.1
- Unknown method on the type name → **E2704**
- If a variable shadows the class name, `.` is ordinary instance member access

Does not add static/type methods without a receiver (that is **0.8.6**).

### 0.8.6 — type methods (no `this`)

Methods that belong to the type, not an instance — factory / helpers.

**Implemented spelling:**

```echo
class Point {
    new { x: int; y: int; }

    fn origin() -> Point {
        return Point { x: 0, y: 0 };
    }

    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }
}

p: Point = Point.origin();
```

Rules:

- No `this` parameter ⇒ type method; call as **`Point.origin()`**
- May not read/write instance fields except through a constructed value
- Type method as value: `Point.origin` is `fn() -> Point` (or with its params)
- Instance methods still require `this` as first param
- Calling/binding a type method through an instance → **E3213**
- Duplicate method names still rejected (covers type/instance name clash)

Does not add free-standing `static` keyword. Absence of `this` is the signal.

### 0.8.7 — optional `implements` clause

Make intended interfaces visible at the class declaration; inference remains.

**Working spelling:**

```echo
interface Named {
    fn name(this) -> str;
}

class User implements Named {
    new {
        id: int;
        label: str;
    }

    fn name(this) -> str {
        return this.label;
    }
}
```

Rules:

- `implements I, J` is **optional**. Omitting it keeps 0.8.2 inferred assignability
- When present, the class must provide every listed interface’s methods (compatible signatures) or abort at analyze time (new **E32xx** or reuse existing type errors)
- Multiple interfaces allowed; order free
- Still **no** class inheritance / `extends`

Does not require `implements` for assignability (inference stays).

### 0.8.8 — docs / examples / README release pass

No new language syntax. Make the public surface match 0.8.0–0.8.7 before shipping.

- README: remove stale “no classes”; install path ready for PyPI (`pipx install echolang` / prefer `echolang` over `echo`)
- Getting started + language reference: `new { }`, defaults, unbound/type methods, optional `implements`
- Capability matrix / known limitations / semantics notes through 0.8.7
- At least one small examples set covering class + interface
- Highlighter / VitePress keyword sync for `new` in class-body context if needed
- Confirm `./build.sh` builds a clean sdist+wheel; dry-run upload to **TestPyPI** encouraged

### 0.8.9 — first PyPI release

Publish **`echolang`** to PyPI. Language surface is whatever 0.8.8 documented.

- Version **0.8.9** in `pyproject.toml` / `__init__.py` / highlighter package
- Tag **`v0.8.9`**
- Upload via `./build.sh --release` (or Trusted Publishing) after full pytest green
- Post-release: docs install section points at PyPI; changelog marks first public package release
- **Do not** publish 0.8.0–0.8.8 to PyPI as the first public versions if avoidable — 0.8.9 is the intentional first upload

### 0.8 open questions

| Topic | Working assumption | Alternatives |
| --- | --- | --- |
| Keyword | `class` (struct-like) — locked | `struct` |
| Construction call | `Point { x: 3, y: 4 }` — locked | `Point.new(...)`; positional `Point(3, 4)` |
| Ctor field block | `new { ... }` — locked in **0.8.3** | keep bare fields forever |
| Receiver name | `this` — locked | `self` |
| Equality | field-wise `==` — locked | identity / `===` later |
| Unbound methods | **0.8.5** — locked | never |
| Type methods | **0.8.6** — locked (no `this`) | `static` keyword |
| Visibility | all public through 0.8.9 | `priv` later (held) |
| `implements` | optional in **0.8.7**; inference remains | required always |
| Inheritance | never in 0.8 | single `extends` later series |
| Class vs exact hash | strictly nominal | convert helpers later |
| First PyPI version | **0.8.9** | 1.0.0 |

### Out of 0.8 (still held globally)

Inheritance trees, abstract classes, generics on classes, operator overloading, properties/`get`/`set`, inner classes, `priv`, and `match` / `Result` remain outside this spine.

## Held (do not implement)

Do not move global holds into 0.7/0.8 polish. **0.8.0–0.8.6 are implemented**; **0.8.7–0.8.9** stay held until started. The closed 0.7 spine is in the **0.7.x** table.

| Item | Status |
| --- | --- |
| Classes / OOP | spine **0.8.0–0.8.2** + polish **0.8.3–0.8.6** done; **0.8.7–0.8.9** drafted |
| Generics | held |
| Async | held |
| VM / JIT | held |
| Packages | held |
| `try` / `catch` | held |
| `Result` / `Option` | held |
| `match` (error / `Result` form) | held — 0.7.6 is `switch` on values |
| User-level failure recovery | designed ([failure model](/failure-model)) — syntax held; `*Or` stdlib implemented (0.5.3) |
| Overloading | held |
| Formatter / `echo fmt` | implemented (0.5.4) |
| Linter / `echo lint` | implemented (0.5.5), expanded (0.5.8) |
| Native test runner / `echo test` | implemented (0.5.6) |
| Multi-path `echo check` | implemented (0.5.9) |
| Editor tasks + Problems matchers | implemented (0.5.7), Check workspace (0.5.9) |
| LSP | held |
| Dates, HTTP, regex | held |
| `mkdir -p` / recursive delete | held |
| Test DSL (`test "name" { }`) | held |
| String `map` / `filter` over graphemes | skipped (awkward) |
