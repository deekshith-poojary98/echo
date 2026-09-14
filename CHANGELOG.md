# Changelog

## 0.7.9

Param `const`. Tenth 0.7 language increment — closes the 0.7.0 gap where parameters stayed mutable. Failure model unchanged. **0.7 polish is complete.** No classes (0.8).

- Spelling: **`fn f(const xs: list) { ... }`** and lambdas **`fn(const xs: list) { ... }`**
- Same rules as binding `const`: no reassignment (**E3201**), no in-place mutation through that name (**E3202**), `use mut` rejected (**E3204**)
- Bound list/hash is **frozen** (shared identity — caller's value is frozen too; later mutation via another name aborts **E3203**)
- Works with defaults, variadics (`const xs: int...`), and destructuring params (`const [a: int, b: int]`)
- Formatter prints `const` before the parameter

## 0.7.8

Hash destructure rest. Ninth 0.7 language increment — polish on 0.7.1. Failure model unchanged. No param `const` yet (0.7.9). No classes.

- Spelling: **`{ id: int, rest: dynamic... }`** — fixed keys bind as usual; leftover keys bind as a **`hash`** named `rest`
- `T...` is the value type for each leftover entry (same idea as list rest element type). Binding type is always `hash`
- Rest must be last. No `as` rename on the rest field (`{ id as extras: dynamic... }` is a parse error)
- Assignment omits types: **`{ id, rest... } = user;`**
- Empty leftovers bind `{}`. Works in declarations, assignment, function parameters, and `switch` hash arms
- Compose with 0.7.7 rename on fixed fields: `{ id as userId: int, rest: dynamic... }`

## 0.7.7

Hash destructure rename. Eighth 0.7 language increment — polish on 0.7.1. Failure model unchanged. No hash rest (still later). No classes.

- Spelling: **`{ id as userId: int }`** — key stays `id`, binding is `userId`. Same-name stays `{ id: int }`
- Assignment omits types: **`{ id as userId } = user;`**
- Works in declarations, assignment, function parameters, and `switch` hash arms
- Keyword **`as`** (exact token; `asInt` and other identifiers stay valid)
- Formatter prints `id as userId: int`. Highlighter treats `as` like `in` / `by`

## 0.7.6

`switch` on values. Seventh 0.7 language increment. Statement-form value dispatch for literals, union member types, and 0.7.1 destructuring. Keyword is **`switch`**, not `match` (`match` stays reserved for a held error/`Result` form). Failure model is unchanged — a failed pattern tries the next arm; abort inside an arm still aborts. No expression-form `switch`.

- Spelling: `switch x { 0 { ... } 1 { ... } else { ... } }`
- Arms: literal equality (`0`, `"ok"`, `true`, `null`), type patterns (`int { }`, `int n { }`), list/hash destructuring (`[a: int, b: int] { }`, `{ id: int } { }`)
- `else` required unless arms exhaust a typed bool (`true` and `false`) or every member of a typed union via type patterns (**E3210** otherwise)
- Soft match: wrong length/key/type on a pattern does not abort the `switch`; the next arm runs. Aborting inside a chosen arm still aborts
- Formatter prints `switch`. Highlighter treats `switch` as a control keyword

## 0.7.5

Union types. Sixth 0.7 language increment. `T | U` is a typed alternative to `dynamic`. Failure model is unchanged — unions are not `Option` / `Result`, and there is no error recovery. No `switch` (0.7.6). No control-flow narrowing yet (`if type(x) == "int"` does not narrow).

- Spelling: `int | str` in type position (`||` stays boolean or). Spaces optional. Members flatten; duplicates drop (`int | str | int` is `int | str`)
- Members may be builtins (`int`, `str`, `bool`, `float`, `list`, `hash`, `dynamic`, `void`), aliases, `fn(...)`, `{ ... }`, and `exact { ... }`
- Assignability: a value is assignable to a union if it matches **any** member. A union is assignable to `C` if **every** member is assignable to `C`. Union to union: each source member is assignable to some target member. `dynamic` still accepts everything
- Echo has no `null` type (`null` is a value typed as `dynamic`). `str | null` does not parse. Prefer `str | void` when a binding may hold `null`. Unions do not add Option
- Runtime assignment / arguments / returns use `matches_type` against any branch. Mismatches report existing codes (**E2001** declarations/assignments, **E2706** arguments, and related return checkpoints)
- Formatter prints `int | str`. Highlighter treats `|` as an operator in types

## 0.7.4

Range as a value. Fifth 0.7 language increment. `start...end` and `start..end` are expressions that produce a `list` of `int`, matching `for` / `rangeList` / `rangeListInclusive`. Failure model is unchanged. No unions or `switch`.

- Exclusive `0...5` is `[0, 1, 2, 3, 4]`; inclusive `0..5` is `[0, 1, 2, 3, 4, 5]`
- Optional `by step` in expression position: `0...10 by 2`, same step rules as `for` (`by 0` aborts)
- Empty when that `for` would not iterate (`0...0` is `[]`; `0..0` is `[0]`)
- Type is `list` (of `int`). Non-int bounds abort like `for` (analyzer rejects clear literal non-ints as **E1015**)
- `for i: int in 0...10` stays the dedicated numeric loop and does not allocate a list. `foreach i: int in 0...10` iterates the allocated list value
- Keep `rangeList` / `rangeListInclusive`; they remain valid and produce the same values as the exclusive / inclusive expressions (step `1`)
- Slice syntax stays colon (`xs[1:4]`); `xs[0...10]` indexes with a list and is a type error

## 0.7.3

Builtins as values. Fourth 0.7 language increment. Named standalone builtins are first-class `fn` values: assign, pass, return, and store them. Failure model is unchanged. No range-as-value, unions, or `switch`.

- Referring to `say`, `map`, `type`, and the other standalone builtins without calling them yields a function value. `say("hi")` and `xs.map(f)` still call as before
- The value’s type is a `fn(...)` matching standalone arity. Variadic builtins are `fn(dynamic...) -> void` (`say`, `eprint`) or `fn(dynamic...) -> str` (`format`, `pathJoin`). Echo has no `null` type, so those returns use `void`. Fixed-arity names use real types where practical (`map`: `fn(list, fn(dynamic) -> dynamic) -> list`; `abs`: `fn(dynamic) -> dynamic` because it accepts int and float). Assignment to a compatible narrower type is allowed (`fn(str) -> dynamic = say`, `fn(list, fn(int) -> int) -> list = map`, `fn(int) -> int = abs`)
- Method form without a call is also a value: `xs.map` is a bound `fn` that already has the receiver. Unknown properties still report **E2704**. Some mutating names (`push`, `pull`, …) remain method-oriented at the call site; prefer `xs.push` over a bare `push`
- `type(say)` is `"fn"`. Equality is by builtin identity/name: `say == say` is true; aliases compare equal to the same builtin. Bound methods compare equal when they wrap the same builtin and the same receiver object
- `const print: fn(str) -> dynamic = say;` cannot be reassigned (**E3201**). The builtin itself is not a mutable object
- Host-denied builtins are still values; **calling** them still aborts **E2801**
- Dispatch builtins such as `filter` (list vs hash) keep runtime dispatch on the first argument / receiver

## 0.7.2

Exact object types. Third 0.7 language increment. Open object types remain open, and exactness does not freeze values. No unions, `switch`, builtins-as-values, range-as-value, or `#{ ... }` syntax.

- `exact { id: int, name: str }` is available inline and in aliases: `type User = exact { id: int, name: str };`
- Exact types require every declared field with its declared type and reject undeclared fields. Nested exact object types are checked recursively
- Exact-shape checks apply at declarations, assignments, function arguments and returns, destructured bindings, and `foreach` bindings
- An exact object type is assignable to a compatible open object type. An open object type is not assignable to an exact type
- Extra fields on an exact type report **E3208**; missing fields report **E3209**. Other type mismatches continue to report the existing checkpoint-specific type error
- `exact` is a formatter-preserved and editor-highlighted keyword

## 0.7.1

Destructuring. Second 0.7 language increment. Failure model is unchanged. No `as` rename, hash rest, exact objects, unions, `switch`, builtins-as-values, or range-as-value.

- List declare: `[a: int, b: int] = pair;`. Hash declare: `{ id: int, name: str } = user;` (keys match field names)
- `const [lo: int, hi: int] = bounds;` freezes each bound value the same way as `const`
- Assignment to already-declared names omits types: `[a, b] = pair;` and `{ id, name } = user;`
- Function parameters: `fn add([a: int, b: int]) -> int` (one `list` argument) and `fn greet({ name: str }) -> str` (one `hash` argument)
- List rest is last, Echo variadic style: `[head: int, rest: int...] = xs` binds `rest` as a `list` of `T`. No hash rest
- Length/shape mismatch aborts (**E3205**), or is a semantic error when the right-hand side is a list/hash literal. Extra list elements without rest abort. Missing hash keys abort (**E2711**, same as `user["x"]`). Extra hash keys are ignored (exact objects are 0.7.2)
- Wrong container type is **E3206** (expected list) or **E3207** (expected hash)
- Nested list patterns such as `[[a: int], b: int]` are supported. No `as` rename
- Playground and highlighter samples include destructuring

## 0.7.0

`const` bindings. First 0.7 language increment. Failure model is unchanged. No destructuring, exact objects, unions, `switch`, builtins-as-values, or range-as-value.

- Spelling is `const name: T = expr;`. Type annotation is required, same as ordinary `name: T =`. The binding must be initialized (`const x: int;` is a parse error)
- Reassignment (`x =`, `x +=`, and the other compound assigns) is a semantic error **E3201**
- In-place mutation through that name (`push`, `xs[i] =`, hash field set, and other mutating builtins) is a semantic error **E3202**
- The bound list or hash is **frozen**. Passing it into a function that mutates it, or aliasing it to a mutable name and mutating, aborts **E3203**. Reading, iterating, and helpers that return a new value (`map`, `unique`, `clone`) are fine
- `export const name: T = expr;` is supported. Ordinary (non-const) exports keep Model A shared mutable identity
- `use mut` on a const binding is **E3204**. `watch` on a const name is legal and will not fire from that binding
- Function parameters stay mutable. `const` on parameters is not in 0.7.0
- Nested collections reached through a different mutable name are not deep-frozen
- Playground and highlighter treat `const` as a keyword

## 0.6.9

Four items in one release: function types honor trailing defaults, list `flatten`, list `partition`, and `echo test --json`. Last 0.6.x slice. No new keywords. Failure model is unchanged. No first-class builtins, `const`, or destructuring.

- A function with trailing defaults is assignable to the full-arity type and to a narrower type that omits those defaulted parameters. Types still spell `fn(int) -> int` (no `?` or default markers). `fn(x: int, y: int = 0) -> int` matches `fn(int) -> int` and `fn(int, int) -> int`, not `fn() -> int`. Calls through the narrower type pass only provided args; defaults apply at call time. Required parameters and variadics still have to match
- `flatten(items: list) -> list` / `items.flatten()` concatenates **one** level of nested lists into a new list. Empty list is `[]`. A top-level non-list element is `E2846`. Input is not mutated. Keyword `items:`
- `partition(items: list, f) -> list` / `items.partition(f)` returns `[matches, rest]`. Unary `f` must return `bool` (`1` is not kept; `E2831`). Empty list is `[[], []]`. Callback abort still aborts. Input is not mutated. Non-function `f` is `E2847`; wrong arity is `E2848`. Keywords `items:` / `f:`
- `echo test --json` writes a machine-readable JSON report to stdout (totals plus per-unit name / pass / fail, with failure message and location when present, and `skipped` from `-run`). Human unit lines and the summary are omitted. Composes with `-run` / `--run` and `--plain`. Exit codes stay 0 / 1 / 2. `echo test.echo` still runs that file
- Playground highlighting tracks `flatten` and `partition`

## 0.6.8

Four items in one release: `echo test -run`, list `chunk`, `rangeList` / `rangeListInclusive`, and hash `mapValues` / `filter`. No new keywords. Failure model is unchanged. No function-type defaults or first-class builtins. `0...10` is still not a list value.

- `echo test -run PATTERN` / `--run PATTERN` runs only zero-arg `fn testXxx()` units whose **function names** match a case-sensitive glob (`*` and exact). `*Add*` matches `testAdd`; `testAdd` matches only `testAdd`. Not file names. Non-matching units are skipped (not failed). A file with no matching units is skipped and does not fail (`0 passed, 0 failed` if nothing ran). Directories / `*_test.echo` still apply. `--plain` is unchanged. `echo test.echo` still runs that file
- `chunk(items: list, size: int) -> list` / `items.chunk(size)` splits into a new list of lists of length `size`; the last chunk may be shorter. Empty list is `[]`. `size` must be an `int` `>= 1` (`E2842`). Input is not mutated. Keyword `items:` / `size:`
- `rangeList(start, end) -> list` is the same integers as `for i in start...end` (exclusive end, step `1`). `rangeListInclusive(start, end)` matches `start..end` (inclusive end). Empty when the `for` would not iterate. Returns a `list` of `int`. Not `0...10` as a value. Keywords `start:` / `end:`. Bounds that are not convertible to `int` abort (`E2843`)
- `mapValues(h, f)` / `h.mapValues(f)` returns a new hash with the same keys; `f` is unary `f(value) -> newValue`. Non-function `f` is `E2844`; wrong arity is `E2845`. Empty hash is `{}`. Input is not mutated. Insertion order is preserved (hashes already preserve it)
- `filter` keeps hash entries where unary `f(value)` is **bool** `true` (not `1`), same rule as lists. Standalone `filter(items, f)` and `items.filter(f)` dispatch on the first argument / receiver: `list` or `hash`. Callback abort still aborts. Codes `E2829`–`E2831` unchanged
- Playground highlighting tracks `chunk`, `rangeList`, `rangeListInclusive`, and `mapValues`

## 0.6.7

List `zip` and `unique`. No new keywords. Failure model is unchanged. No function-type defaults or first-class builtins. `unique` was originally queued as 0.6.8 and ships here.

- `zip(left: list, right: list) -> list` returns a new list of 2-element lists `[left[i], right[i]]`. Length is `min(len(left), len(right))`; unequal lengths are not an error. Empty either side is `[]`. Inputs are not mutated
- Method form: `left.zip(right)`. Keywords `left:` / `right:` on the standalone call. List only. No N-way zip and no zipper callback
- `unique(items: list) -> list` returns a new list of first occurrences in original order, using Echo `==` (`true` is not `1`). Empty list is `[]`. Input is not mutated
- Method form: `items.unique()`. Keyword `items:` on the standalone call. List only
- `zip` / `unique` are calls, not assignable values
- Playground highlighting tracks `zip` and `unique`

## 0.6.6

Optional slice bounds on the `xs[1:4]` syntax from 0.6.0. Same abort rules as `slice()`. No step form. Failure model is unchanged. No zip, unique, or first-class builtins.

- `xs[a:]` omits end (`length`); `xs[:b]` omits start (`0`); `xs[:]` is `slice(0, length)` — a shallow list copy or the full string
- Colon is still required (`xs[]` is not a slice). Single index `xs[i]` is unchanged. There is no `xs[1::2]` step syntax
- Bounds still `[0, length]`, end exclusive, no negatives; out of range aborts. Lists and strings, matching `slice()`
- Formatter preserves omitted bounds (`xs[1:]`, not invented `0` / `len`)
- Playground Lambdas & lists example and highlighter sample include optional-bound slices

## 0.6.5

List `some` / `every` / `findIndex` on function values from 0.6.0. Same bool rule as `filter`. No new keywords. Failure model is unchanged — a callback that aborts still aborts the whole call. `find(value)` stays value search. No zip, optional slice bounds, or first-class builtins.

- `some(items: list, f: fn(T) -> bool) -> bool` is `true` if any element matches (`bool` only — not truthy `1`). Empty list is `false`
- `every(items: list, f: fn(T) -> bool) -> bool` is `true` if all elements match. Empty list is `true`
- `findIndex(items: list, f: fn(T) -> bool) -> int` is the first matching index, or `-1` if none
- Method form: `items.some(f)` / `items.every(f)` / `items.findIndex(f)`. List only. Input is not mutated. Short-circuit: `some` and `findIndex` stop on the first `true`; `every` stops on the first `false`
- `f` is a function value (named `fn` or lambda) with **exactly one** parameter. Defaults and extra variadics do not count toward that arity. Not a name string
- Non-`bool` callback result reuses `filter`'s `E2831`. Wrong callback type is `E2840`; wrong arity is `E2841`
- `some` / `every` / `findIndex` are calls, not assignable values
- Playground highlighting tracks `map` / `filter` / `reduce` / `forEach` / `flatMap` / `some` / `every` / `findIndex`, lambdas, `fn` types, `...` variadics, and `xs[1:4]`

## 0.6.4

List `flatMap` on function values from 0.6.0. No new keywords. Failure model is unchanged — a callback that aborts still aborts the whole call. No some/every, findIndex, or first-class builtins.

- `flatMap(items: list, f: fn(T) -> list) -> list` applies unary `f` to each element and concatenates the returned lists one level into a new list
- Method form: `items.flatMap(f)`. List only. Empty list returns `[]` and does not call `f`. Input is not mutated
- `f` is a function value (named `fn` or lambda) with **exactly one** parameter. Defaults and extra variadics do not count toward that arity. Not a name string
- Each callback result must be a `list` (`E2839`). Wrong callback type is `E2837`; wrong arity is `E2838`
- `flatMap` is a call, not an assignable value

## 0.6.3

List `forEach` on function values from 0.6.0. No new keywords. Failure model is unchanged — a callback that aborts still aborts the whole call. No flatMap, some/every, or first-class builtins.

- `forEach(items: list, f: fn(T) -> _) -> null` calls unary `f` on each element and discards the return value
- Method form: `items.forEach(f)`. List only. Empty list does not call `f` and returns `null`. Input is not mutated
- `f` is a function value (named `fn` or lambda) with **exactly one** parameter. Defaults and extra variadics do not count toward that arity. Not a name string
- Wrong callback type is `E2835`; wrong arity is `E2836`
- `forEach` is a call, not an assignable value

## 0.6.2

List `reduce` on function values from 0.6.0. No new keywords. Failure model is unchanged — a callback that aborts still aborts the whole call. No forEach, flatMap, fold twin, or first-class builtins.

- `reduce(items: list, init, f: fn(acc, item) -> acc) -> acc` folds `f` over `items` starting from required `init`
- Method form: `items.reduce(init, f)`. List only. Empty list returns `init` and does not call `f`. Input is not mutated
- `f` is a function value (named `fn` or lambda) with **exactly two** parameters. Defaults and extra variadics do not count toward that arity. Not a name string
- Each callback result must match `init`'s type (`E2834`). Wrong callback type is `E2832`; wrong arity is `E2833`
- `reduce` is a call, not an assignable value

## 0.6.1

List `map` / `filter` on function values from 0.6.0. No new keywords. Failure model is unchanged — a callback that aborts still aborts the whole call. No reduce/fold, flatMap, forEach, or first-class builtins.

- `map(items: list, f: fn(T) -> U) -> list` applies `f` to each element and returns a new list
- `filter(items: list, f: fn(T) -> bool) -> list` keeps elements where `f` returns `true` (`bool` only — not truthy `1`)
- Method form: `items.map(f)` / `items.filter(f)`. List only. Empty list returns empty list. Input is not mutated
- Wrong arity or type of `f` is a type/runtime error. `map` / `filter` are calls, not assignable values

## 0.6.0

Language release: first-class functions including lambdas, slice syntax, and user `fn` defaults plus variadics. Failure model is unchanged — callback or default expressions that abort still abort. No `map` / `filter`, `try` / `catch`, classes, or overloading.

- Named functions are values. Lambdas spell `fn(x: int) -> int { ... }` (inline `=>` also works). The function type is `fn(int) -> int`
- `order(comparator)` accepts a function value, a lambda, or a function name string
- Slice syntax `xs[1:4]` (colon, both bounds required) desugars to `slice(start, end)` with the same abort/bounds rules. `xs[1:]`, `xs[:4]`, and `xs[:]` are parse errors
- User `fn` default parameters (`punct: str = "!"`) and a trailing variadic (`parts: int...`, bound as a `list` of `T`) ship together. Defaults come before the variadic and are evaluated at call time when omitted
- Formatter, linter, REPL continuation (parens/brackets as well as braces), and highlighter track the new surface

## 0.5.9

Last 0.5.x tooling slice. `echo check` accepts the same multi-path layout as `fmt` / `lint` / `test`. No language change.

- `echo check [paths...]` analyzes files or recursively `*.echo` directories without running them. Explicit file paths always check
- Exit 0 if every file is clean; 1 if any file fails parse or semantic analysis. After a failure, continue so `echo check .` prints every diagnostic, then exit 1
- Missing path prints an error and exits 1; no path prints help and exits 2
- The first argument must be the word `check`; `echo check.echo` still runs a file named `check.echo`. `--plain` is unchanged
- Editor: **Echo: Check workspace** runs `echolang check --plain` on `${workspaceFolder}` with the `$echo` matcher. **Echo: Check file** remains

## 0.5.8

A small `echo lint` rule expansion. Same finding format. Not a second typechecker.

- New rules: `test-naming` (top-level `fn` that looks like a test but is not a zero-arg `testXxx` unit), `self-assign` (`x = x` / `x = x + 0` / `x = 0 + x`), and `unreachable-after-fail` (later statements in the same block after `fail(...)` or `return`)
- Unused parameters stay `unused-local`; there is no separate `unused-param` rule
- `unused-export` is not shipped: exports are for other files, and Echo has no file-local convention that would distinguish a dead export from a library API
- `redundant-parens` is not shipped: the parser drops grouping parentheses, so the AST cannot see what the formatter would omit
- Findings still print `path:line:col: rule: message`. Matcher `$echo-lint` is unchanged

## 0.5.7

Editor integration for the fmt / lint / test / check CLI (not an LSP).

- The VS Code / Cursor extension `echo-syntax-highlighter/` contributes tasks, problem matchers, and commands that run `echolang check` / `fmt` / `lint` / `test` with `--plain` so diagnostics land in the Problems panel
- Matchers cover `Error[E####]` / `Error:` plus `--> file:line:col` (check and parse errors), lint `path:line:col: rule: message`, and `echo test` failures that include a location
- Format Document shells out to `echolang fmt`; this is not a language server, completions, or jump-to-definition
- Install the Echo CLI (`echolang` on PATH). The Unix `echo` builtin is not the language

## 0.5.6

Native `echo test` product: expect-style helpers, file and function units, pass/fail summary. No new keywords. No `test "name" { }` syntax.

- `echo test [paths...]` runs files or recursively discovers `*_test.echo` in directories. Explicit file paths always run, even if they are not named `*_test.echo`. No path prints help and exits 2
- Zero-argument top-level `fn testXxx()` functions are separate units (Go-shaped). Other top-level statements run once as setup, or as the file unit when there are no `test*` functions
- `expect(cond, message)`, `expectEq(left, right, message)`, and `expectNeq(left, right, message)` record a failure and continue under `echo test`. Outside a test run they abort like `assert`. `cond` must be `bool`. Codes **E2826** / **E2827** / **E2828**
- `assert` / `fail` still abort the current unit. Later units still run. The runner exits 0 if every unit passed and 1 if any failed (including `exit(n)` with n ≠ 0)
- Summary lines look like `ok   path/foo_test.echo::testAdd` / `FAIL path/foo_test.echo::testSub` then `N passed, M failed`
- The first argument must be the word `test`; `echo test.echo` still runs a file named `test.echo`

## 0.5.5

`fail(message)` and `echo lint`. No new syntax. No `try` / `catch`.

- `fail(message)` always aborts with an Echo error; `message` must be `str`. Not recoverable. No `*Or` twin. Error code **E2825**
- `echo lint [paths...]` reports style findings without running the program: unused locals/functions/imports, comparison to boolean literals, redundant `by 1`, empty if/function bodies, and names that shadow builtins
- Dirty lint findings print `path:line:col: rule: message` and exit 1; a clean tree exits 0
- A directory argument lints `*.echo` recursively; parse errors use the same diagnostic as `echo check`; no path prints help and exits 2
- The first argument must be the word `lint`; `echo lint.echo` still runs a file named `lint.echo`. `fail` is a builtin, not a CLI command, so `echo fail.echo` still runs that file

## 0.5.4

Canonical `echo fmt`. No language change.

- `echo fmt [paths...]` rewrites Echo sources in place: 4-space indent, comments kept, `else if` flattening, parentheses from operator precedence
- `echo fmt --check` prints paths that would change and exits 1; already-formatted files exit 0
- A directory argument formats `*.echo` files recursively; no path prints help and exits 2
- Parse errors print the same diagnostic as `echo check` and do not write a broken file
- The first argument must be the word `fmt`; `echo fmt.echo` still runs a file named `fmt.echo`
- Number literals may be respelled (`1e3` → `1000.0`); strings are wrapped from raw lexemes and are not re-escaped

## 0.5.3

Fallback `*Or` twins for untrusted input. Aborting originals are unchanged. No `try` / `catch`. No `Result` type.

- `readFileOr(path, fallback)` returns file text on success and `fallback` for missing files, invalid UTF-8, directories, and other read OS errors
- Restricted hosts still deny `readFileOr` with E2801; a non-string path is still a type error
- `parseJsonOr(text, fallback)` returns the parsed value or `fallback` for invalid JSON; non-string text is still a type error
- `asIntOr(value, fallback)` / `asFloatOr(value, fallback)` return the converted number or `fallback` for unparseable strings, `null`, lists, and hashes
- `asIntOr(true, 0)` / `asFloatOr(true, 0.0)` stay type errors — bool has no twin
- `readFile`, `parseJson`, `asInt`, and `asFloat` still abort

## 0.5.2

REPL session state. One `echo` process keeps one environment for the lifetime of the REPL.

- Bindings, functions, and type aliases persist across submissions; builtins stay available
- Analyzer scope is seeded from prior successful submissions so later snippets can use earlier names
- A failed lex/parse/semantic/runtime submission does not drop earlier bindings; analyze failures are not executed
- A runtime error does not roll back the interpreter: `x: int = 1; bad();` may leave `x` assigned even though that submission failed
- `import` in the REPL loads sibling `.echo` files from the working directory into the session
- `use mut` works for variables declared earlier in the session
- `exit(code)`, EOF, `--plain`, and brace/triple continuation are unchanged

## 0.5.1

Harden the 0.5.0 CLI and restricted host. No new language features.

- REPL continues while `{` is unclosed and while a triple-quoted string is unterminated
- Empty REPL lines are ignored; `exit(code)` and EOF (Ctrl-D) leave without a Python traceback
- A failed REPL submission returns to the prompt instead of killing the process
- `echo test` with no path prints help and exits 2; `exit(2)` in a test file is a failed test; imports execute
- `Host.run_process` refuses to launch when `allow_run=False` (playground policy)

## 0.5.0

Language basics. Syntax and stdlib together: this is **0.5.0** because multiline strings and `.5` / scientific number literals change the grammar. Builtins-only would have been 0.4.4.

- `assert(cond, message)` aborts with an Echo error when `cond` is falsy; `message` must be `str`
- `copyFile(src, dest)` binary-copies a file; restricted hosts deny it
- `pathJoin(...)` joins 2+ path parts with pathlib; available in the playground
- `run(command, args)` runs a process without a shell and returns `{ code, stdout, stderr }`; `Host.allow_run` defaults true; playground sets `allow_run=False`
- `now()` returns unix time as `int` seconds
- `random()` is a float in `[0, 1)`; `randomInt(min, max)` is inclusive
- Triple-quoted `"""` / `'''` strings may span lines and still interpolate `${...}`
- Number literals `.5`, `1e3`, and `1e-3`; `5.` stays integer-then-dot
- `readLine()` reads one stdin line; EOF aborts
- `echo` with no file starts a REPL (`--plain` supported)
- `echo test path.echo` runs a file; exit 0 is pass

## 0.4.3

Host and stdlib depth. No new syntax.

- `mkdir(path)` creates the leaf directory only; missing parent, existing path, and a file in the way abort
- `removeFile(path)` deletes a file; missing paths and directories abort
- Restricted hosts deny `mkdir` and `removeFile` the same way they deny `readFile`
- String `indexOf` / `lastIndexOf` (missing → `-1`; empty part → `0` / length)
- String `repeat`, `padStart` / `padEnd`, and `replaceFirst`
- Numeric `abs`, `min(a, b)`, `max(a, b)`, `floor`, and `ceil` (reject `bool`)
- `eprint(...)` writes to stderr the same way `say` writes to stdout

## 0.4.2

Host completeness for scripts. No new syntax.

- `cwd()` returns the host working directory as a string
- `exit(code)` stops the program with that process code and no error diagnostic
- `isDir(path)` returns `bool` and does not abort when the path is missing
- `listFiles(path)` returns sorted directory entry names; missing paths and files abort
- Restricted hosts deny `isDir` and `listFiles` the same way they deny `readFile`

## 0.4.1

Stdlib and tooling depth. No new syntax.

- `join(separator)` on a list of strings
- `startsWith` / `endsWith` on strings
- `fileExists(path)` returns `bool` and does not abort when the file is missing
- `echo check file.echo` analyzes without executing
- Restricted hosts still deny `fileExists` the same way they deny `readFile`

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
