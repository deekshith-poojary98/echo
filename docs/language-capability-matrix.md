# Echo Language Capability Matrix

**Status:** Living audit against `src/echo/` and tests. Not a language contract.
**Aligned through:** v0.8.6 (type methods). Earlier rows for field defaults, `new { ... }`, interfaces, methods/`this`, nominal classes, param `const`, hash rest/rename, `switch`, unions, const, destructure, exact, builtins-as-values, range-as-value, modules, REPL, fmt/lint/test, `*Or`, map/filter stay marked as shipped.
**Contracts win:** `docs/language-semantics.md`, `docs/module-semantics.md`, `docs/failure-model.md`.
**v0.4 boundary:** Frozen in [archive/v0.4-language-vs-stdlib](/archive/v0.4-language-vs-stdlib) (host + stdlib). 0.5–0.8 added syntax and tooling on top of that cut.

Not a promise list. A gap here is either a hole, a hold, or already closed — check the status column before treating it as work.

---

## How to read a row

| Field | Meaning |
| --- | --- |
| **Status** | Current implementation, judged against the contracts and `src/echo/` |
| **Supported** | End-to-end: syntax, semantics, runtime, and tests |
| **Partial** | Present, but incomplete for real programs |
| **Missing** | Not in the language or stdlib today |
| **Excluded** | Absent on purpose |
| **Priority** | Whether we should care soon. “Don’t touch” means leave it alone |
| **Possible version** | A guess, or the version that shipped it. Not a commitment for open rows |

---

## Snapshot (through v0.8.6)

Fundamentals are in: typed bindings, control flow (including `switch`), loops, functions/lambdas,
`const` (including param `const`), destructuring (hash `as` rename and hash rest), exact object types, unions, range expressions as
lists, lexical scope, closures, collections, strings (including multiline),
`use` / `use mut`, `watch`, sibling-file modules, Echo-owned errors,
nominal `class` + construction + methods/`this` + `interface` (no inheritance).

Host/stdlib and tooling that used to be the main gaps: `args` / `env` / files /
JSON, inquiry + `*Or` twins, `echo check` / `fmt` / `lint` / `test`, REPL.

Still open or held: richer date/time, package manager, LSP, `try` / `catch`,
generics, VM, class inheritance. Failure model is frozen — abort by default; recovery is
inquiry and `*Or`, not exceptions.

| Bucket | Verdict |
| --- | --- |
| Language fundamentals | Supported through 0.8.6 surface |
| Language usability | Host/stdlib mostly shipped; date/time and some sugar still open |
| Language ecosystem | fmt / lint / test / REPL / check shipped; no package manager or LSP |
| Implementation / runtime maturity | Don’t touch (no VM / JIT / native) |

Distinctive on purpose:

- `watch` as a language construct
- `use` / `use mut` instead of implicit outer mutation
- runtime-checked declarations without a static compiler
- `import` / `export` kept separate from `use`
- Model A: imported bindings are immutable; imported collections share identity
- Abort + inquiry + `*Or` instead of `try` / `catch`

---

## Summary

| Capability | Bucket | Status | Priority | Possible version |
| --- | --- | --- | --- | --- |
| Variables | Fundamentals | Supported | Frozen | Done (v0.2) |
| Immutable bindings | Fundamentals | Supported (0.7.0) | Frozen | 0.7.0 |
| Primitive types | Fundamentals | Supported | Frozen | Done |
| Type checking | Fundamentals | Supported | Frozen | Done |
| Type aliases | Fundamentals | Supported (exact 0.7.2, unions 0.7.5) | Frozen | 0.7.5 |
| Arithmetic | Fundamentals | Supported | Frozen | Done |
| Comparisons | Fundamentals | Supported | Frozen | Done |
| Boolean logic | Fundamentals | Supported | Frozen | Done |
| Strings | Fundamentals | Supported (multiline 0.5.0) | Frozen | 0.5.0 |
| Lists | Fundamentals | Supported | Frozen | Done |
| Hashes | Fundamentals | Supported | Frozen | Done |
| Indexing | Fundamentals | Supported | Frozen | Done |
| Control flow | Fundamentals | Supported | Frozen | Done |
| Loops | Fundamentals | Supported; range-as-value 0.7.4 | Frozen | 0.7.4 |
| Loop control | Fundamentals | Supported | Frozen | Done |
| Functions | Fundamentals | Supported | Frozen | Done |
| Recursion | Fundamentals | Partial | Later | Later |
| Closures | Fundamentals | Supported | Frozen | Done |
| First-class functions | Fundamentals | Supported (0.6.0), builtins as values (0.7.3) | Frozen | 0.7.3 |
| Scope | Fundamentals | Supported | Frozen | Done |
| Mutation (`use` / `use mut`) | Fundamentals | Supported | Frozen | Done |
| Modules | Fundamentals | Supported | Frozen | Done (v0.3) |
| Visibility | Fundamentals | Supported | Frozen | Done (v0.3) |
| Language errors | Fundamentals | Partial | Later | Later |
| `watch` | Fundamentals | Supported | Frozen | Done |
| Type conversion | Usability | Supported (`*Or` 0.5.3) | Frozen | 0.5.3 |
| File I/O | Usability | Supported (0.4+) | Frozen | Done |
| User error handling | Usability | Partial (inquiry + `*Or`; no `try`/`catch`) | Design hold | Failure model frozen |
| Exceptions (`try/catch`) | Usability | Excluded | Design hold | Hold |
| Destructuring | Usability | Supported (0.7.1) | Frozen | 0.7.1 |
| Exact object types | Usability | Supported (0.7.2) | Frozen | 0.7.2 |
| Union types | Usability | Supported (0.7.5) | Frozen | 0.7.5 |
| Collection operations | Usability | Supported through 0.6.9 HOFs; range expr 0.7.4 | Frozen | 0.7.4 |
| String utilities | Usability | Supported (0.4+) | Frozen | Done |
| Date / time | Usability | Missing (`now` / `wait` only) | Later | Later (library) |
| Environment variables | Usability | Supported (0.4) | Frozen | Done |
| Program CLI arguments | Usability | Supported (0.4) | Frozen | Done |
| Default / variadic args | Usability | Supported (0.6.0) | Frozen | 0.6.0 |
| Function overloading | Usability | Excluded | Design hold | Hold |
| JSON / interchange | Usability | Supported (0.4); `parseJsonOr` 0.5.3 | Frozen | Done |
| Multiline strings | Usability | Supported (0.5.0) | Frozen | 0.5.0 |
| Package manager | Ecosystem | Missing | Tooling | Tooling track |
| Formatter | Ecosystem | Implemented (0.5.4) | Tooling | 0.5.4 |
| Linter | Ecosystem | Implemented (0.5.8) | Tooling | 0.5.8 |
| Native test runner | Ecosystem | Implemented (0.5.6), `-run` (0.6.8), `--json` (0.6.9) | Tooling | 0.6.9 |
| Debugger | Ecosystem | Partial (`watch` only) | Tooling | Later |
| Documentation generator | Ecosystem | Missing | Tooling | Later |
| IDE support | Ecosystem | Partial (0.5.7), Check workspace (0.5.9) | Tooling | 0.5.9 |
| Language server | Ecosystem | Missing | Tooling | Later |
| REPL | Ecosystem | Supported (0.5.0) | Tooling | Done |
| Playground | Ecosystem | Partial (browser host; no files/argv) | Tooling | Done enough |
| Compiler / native exe | Runtime | Missing | Don't touch | Not now |
| Bytecode / VM | Runtime | Missing | Don't touch | Not now |
| JIT | Runtime | Missing | Don't touch | Not now |
| Concurrency / async | Runtime | Missing | Don't touch | Not now |
| Generics | Runtime | Missing | Don't touch | Not now |
| Classes / OOP | Runtime | Supported (0.8.6; no inheritance) | Active | 0.8.x |
| Structs / records | Runtime | Partial (aliases / exact / class fields) | Later | 0.8.0 |
| Garbage collection | Runtime | Partial | Don't touch | Python-owned |

---

## 1. Language fundamentals

Core surface. Mostly frozen since v0.2–v0.3; 0.6–0.7 fill-ins noted per row.

### Variables

**What it means.** Introduce a name, give it a type, assign, reassign.

**Echo status.** Supported.

**Current syntax.**

```echo
name: str = "Echo";
name = "Echo 2";
```

**Limitations.** A name must be declared before assignment. Redeclaration
in the same scope is an error. Child blocks may shadow.

**Priority.** Frozen.

**Possible version.** Done (v0.2).

---

### Immutable bindings

**What it means.** Prevent reassignment of a name.

**Echo status.** Supported (0.7.0 bindings; 0.7.9 param `const`).

`const name: T = expr;` is declaration-site immutability. Types are required.
The binding must be initialized. Reassignment is **E3201**. Mutation through
that name is **E3202**. The bound list or hash is frozen (**E3203** if mutated
through another name). `export const` is supported. Parameters may be
`const` (`fn f(const xs: list)`) as of 0.7.9. Nested collections via a different
mutable name are not deep-frozen.

Other immutability remains:

- `use name;` inside a function is read-only
- imported module bindings cannot be rebound (v0.3 Model A); ordinary imported
  collections stay mutable in place

**Current syntax.**

```echo
const count: int = 0;
export const pi: int = 3;

fn lock(const xs: list) {
    say(xs);
}

fn read_only() {
    use count;
    // count = 1;   // mutation error
}
```

**Limitations.** Nested values
inside a frozen collection are not recursively frozen.

**Priority.** Done for 0.7.0.

**Possible version.** 0.7.0.

---

### Primitive types

**What it means.** A small set of first-class values.

**Echo status.** Supported.

Echo values: `int` (arbitrary precision), `float` (IEEE-754 binary64),
`str`, `bool`, `null`, `list`, `hash`, and named function values in the
runtime. `bool` is not a subtype of `int`. `null` is a value, not “missing”.
`dynamic` accepts any Echo value. `void` is only a return annotation.

**Current syntax.** `count: int = 1;`, `ok: bool = true;`, `x: dynamic = null;`

**Limitations.** No unsigned ints, decimals, chars, or bytes. Number
literals do not include `.5` or `1e3`.

**Priority.** Frozen.

**Possible version.** Done.

---

### Type checking

**What it means.** Meaningful type errors when values do not match annotations.

**Echo status.** Supported.

Echo is **not** statically typed. Checks happen at declaration, assignment,
argument binding, annotated return, and `foreach` item binding. Unknown
type names are errors.

**Current syntax.** `fn add(a: int, b: int) -> int { return a + b; }`

**Limitations.** No compile-time exhaustiveness. Type aliases are names
for existing types, not new runtime types.

**Priority.** Frozen.

**Possible version.** Done.

---

### Type aliases

**What it means.** Name an existing type, including a structural object shape.

**Echo status.** Supported (exact 0.7.2, unions 0.7.5).

```echo
type Age = int;
type User = { id: int, name: str };
type ExactUser = exact { id: int, name: str };
type Id = int | str;
```

Open object aliases require the listed fields and types and allow extras.
Exact object aliases require precisely the listed fields and types. Exactness
nests and does not freeze values. Exact objects are assignable to compatible
open object types; open objects are not assignable to exact types. Aliases are
not new runtime types.

Union aliases accept a value assignable to any member; a union assigned to a
narrower type requires every member to be assignable. Echo has no `null` type
member — prefer `str | void` when a binding may hold `null`.

**Limitations.** No nominal types and no methods on aliases. No control-flow
narrowing on unions via `if type(x) == "..."` yet (`switch` type arms ship in 0.7.6).

**Priority.** Frozen.

**Possible version.** Exact objects in 0.7.2; unions in 0.7.5.

---

### Arithmetic

**What it means.** `+ - * / %` and unary `-`.

**Echo status.** Supported.

`int / int` truncates toward zero and returns `int`. Other `/` is float
division. Compound assignment exists. Division or modulo by zero is an
Echo runtime error. `"a" + "b"` concatenates. `[1] + [2]` concatenates.
Mixed `str + int` is a type error, not a Python leak.

**Priority.** Frozen.

**Possible version.** Done.

---

### Comparisons

**What it means.** `== != < > <= >=`

**Echo status.** Supported.

`true == 1` is `false`. `null == null` is `true`. Lists and hashes compare
structurally.

**Priority.** Frozen.

**Possible version.** Done.

---

### Boolean logic

**What it means.** Conjunction, disjunction, negation, with defined truthiness.

**Echo status.** Supported.

Operators: `&&`, `||`, `!`. They short-circuit. Falsy values: `false`,
`null`, `0`, `0.0`, `""`, `[]`, `{}`.

**Limitations.** No `and` / `or` / `not` keywords. That is spelling, not a hole.

**Priority.** Frozen.

**Possible version.** Done.

---

### Strings

**What it means.** Create, concatenate, interpolate.

**Echo status.** Supported (multiline 0.5.0).

Quotes: `"..."`, `'...'`, and triple-quoted `"""` / `'''` (may span lines).
Interpolation `${expression}` works in all of them. Escapes: `\\`, `\"`,
`\'`, `\n`, `\t`, `\r`. Number literals also accept `.5` and scientific form
as of 0.5.0.

**Limitations.** No raw-string spelling beyond triples. Interpolation
tokenization is not fully strict (see known limitations).

**Priority.** Frozen.

**Possible version.** Multiline in 0.5.0.

---

### Lists

**What it means.** Ordered mutable sequence: create, access, modify.

**Echo status.** Supported.

Built-ins include `push`, `insertAt`, `pull`, `removeValue`, `empty`,
`find`, `countOf`, `order`, `clone`, `merge`, `reverse`, `length`,
`map`, `filter`, `reduce`, `forEach`, `flatMap`, `some`, `every`, `findIndex`,
`zip`, `unique`, `chunk`, `flatten`, `partition`, plus `rangeList` /
`rangeListInclusive`.

**Limitations.** `clone()` is shallow. Slice syntax `xs[1:4]` (optional
bounds `xs[1:]` / `xs[:4]` / `xs[:]` as of 0.6.6) desugars to `slice()`.
`order(comparator)` accepts a function
value, a lambda, or a function name string. `map` / `filter` take a unary
function value or lambda; `filter` requires a `bool` return. `reduce` takes
a binary function value or lambda and a required `init`. `forEach` takes a
unary function value or lambda, discards the callback return, and yields `null`.
`flatMap` takes a unary function value or lambda that must return a `list`,
and concatenates those lists one level.
`some` / `every` / `findIndex` take a unary function value or lambda that
must return `bool`; `find(value)` stays value search.
`zip` pairs two lists to the shorter length. `unique` keeps first
occurrences in order using Echo `==`.
`removeValue` errors if the value is missing (contract); some older docs
still say it is a no-op.

**Priority.** Frozen.

**Possible version.** Done.

---

### Hashes

**What it means.** String-key maps: create, access, modify.

**Echo status.** Supported.

Built-ins include `keys`, `values`, `pairs`, `ensure`, `take`,
`take_last`, `wipe`, `merge`, `clone`, `mapValues`, `filter`.

**Limitations.** Runtime indexing keys must be `str`. No int keys, no
nested-path syntax.

**Priority.** Frozen.

**Possible version.** Done.

---

### Indexing

**What it means.** `list[0]`, `map["x"]`, nested assignment.

**Echo status.** Supported.

List indexes are `int` in `[0, length)`. Hash keys in `[]` must be `str`.
Out-of-range and missing keys are Echo errors. Indexed assignment follows
`use mut` rules.

**Priority.** Frozen.

**Possible version.** Done.

---

### Control flow

**What it means.** Conditional execution.

**Echo status.** Supported.

`if`, `else`, `else if`, `switch`. Conditions use truthiness. Blocks are scoped.
`switch` is statement-form value dispatch (literals, type arms, destructuring);
failed patterns fall through; **E3210** when `else` is required and missing.

**Limitations.** No expression-form `switch`. No `match` (held for error/`Result` form).

**Priority.** Frozen.

**Possible version.** `switch` in 0.7.6.

---

### Loops

**What it means.** Repeat work.

**Echo status.** Supported.

- `while cond { }`
- `for i: int in start..end by step { }` — `..` inclusive, `...` exclusive
- `foreach item: T in iterable { }` — `list` or `hash` (keys as `str`)
- Range expressions `start...end` / `start..end` (optional `by step`) are
  `list` of `int` values (0.7.4). `for` does not allocate; `foreach` over a
  range expression does

`by 0` is a runtime error. Non-numeric bounds are not convertible.

**Limitations.** No iterator protocol beyond lists/hashes. No infinite
`loop` keyword.

**Priority.** Frozen.

**Possible version.** Range-as-value in 0.7.4; loops otherwise since v0.2.

**What it means.** `break` and `continue`.

**Echo status.** Supported.

Both are only valid inside loops. The analyzer rejects them elsewhere.

**Limitations.** No labeled break. No `break value`. Those are extras,
not the basic expectation.

**Priority.** Frozen.

**Possible version.** Done.

---

### Functions

**What it means.** Named callable with parameters and return values.

**Echo status.** Supported.

```echo
fn add(a: int, b: int) -> int {
    return a + b;
}

fn square(x: int) -> int => x * x;
```

Every parameter needs a type. `return` requires a return annotation.
Calls support positional and keyword arguments. Missing, extra,
unexpected, and duplicate arguments are semantic errors.
Default parameters (`name: T = expr`) and a trailing variadic
(`rest: T...`) shipped in 0.6.0. Overloading stays held.

**Limitations.** No overloads.

**Priority.** Frozen.

**Possible version.** Done.

---

### Recursion

**What it means.** A function may call itself.

**Echo status.** Partial.

The contract allows recursion. `fact(5)` works. The interpreter is a
tree-walk on the Python call stack. Deep recursion can hit Python’s
recursion limit, and that path is not a documented Echo error.

**Current syntax.** Ordinary self-calls.

**Limitations.** No tail-call guarantee. Depth is an implementation limit.

**Priority.** Later. Do not add a VM to “fix” this.

**Possible version.** Later (Echo-owned stack overflow error, maybe).

---

### Closures

**What it means.** Nested functions capture the defining environment.

**Echo status.** Supported.

A call’s parent environment is the definition site, not the call site.
Reads of outer names are allowed. Reassignment and collection mutation
of outer names require `use mut` in **that** function. Nested functions
do not inherit `use mut`.

**Priority.** Frozen.

**Possible version.** Done.

---

### First-class functions

**What it means.** Functions are values: assign, pass, return, store.

**Echo status.** Supported (0.6.0). Builtins as values in 0.7.3.

Named functions are values. Lambdas use `fn(x: int) -> int { ... }`.
The function type spelling is `fn(int) -> int` (no default markers).
As of 0.6.9, a function with trailing defaults is assignable to the
full-arity type and to a narrower type that omits those defaulted
parameters. Required parameters and variadics still have to match.
As of 0.7.3, standalone builtins (`say`, `map`, `type`, …) are also
`fn` values: assign, pass, return, and store. Variadic builtins are
`fn(dynamic...) -> void` (`say` / `eprint`) or `fn(dynamic...) -> str`
(`format` / `pathJoin`). Bound methods such as `xs.map` are values;
unknown properties still error. Equality is the same builtin (or the
same bound receiver). `const` of a builtin alias cannot be reassigned.
Host-denied builtins remain values; calling them still aborts.
`order(comparator)` still accepts a function value, a lambda, or a name
string. List `map` / `filter` take a unary function value or lambda. List
`reduce` takes a binary function value or lambda and a required `init`. List
`forEach` takes a unary function value or lambda, discards the callback
return, and yields `null`. List `flatMap` takes a unary function value or
lambda that must return a `list`, and concatenates those lists one level.
List `flatten` concatenates one level of nested lists. List `partition`
splits a list into `[matches, rest]` with a unary `bool` predicate. List
`some` / `every` / `findIndex` take a unary `bool` predicate; `find(value)`
stays value search. List `zip` pairs two lists to min length. List `unique`
keeps first occurrences in order using Echo `==`.

```echo
double: fn(int) -> int = fn(x: int) -> int { return x * 2; };
say(map([1, 2, 3], double));
print: fn(str) -> dynamic = say;
print("hi");
```

**Limitations.** No overloading.

**Priority.** Frozen.

**Possible version.** 0.6.0; builtins as values in 0.7.3.

---

### Scope

**What it means.** Predictable name resolution.

**Echo status.** Supported.

Lexical scoping. Innermost enclosing declaration at the definition site.
`if` / `else` / `while` / `for` / `foreach` create block scopes.
Function scope parent is the closure. User declarations may shadow builtins.

**Priority.** Frozen.

**Possible version.** Done.

---

### Mutation (`use` / `use mut`)

**What it means.** Outer writes are explicit.

**Echo status.** Supported.

```echo
count: int = 0;

fn bump() {
    use mut count;
    count = count + 1;
}
```

`use` / `use mut` are only valid inside functions. They are **not**
module imports. v0.3 Model A: same-module collection writes still need
`use mut`. Imported bindings are immutable; imported collections share
object identity and may be mutated.

**Priority.** Frozen.

**Possible version.** Done.

---

### Modules

**What it means.** Split a program across files with a defined load model.

**Echo status.** Supported, in the small v0.3 form.

```echo
import add from "math";
```

Bare sibling name. `.echo` implied. Each file is a module. Each module
executes at most once. Cycles are rejected (E3003). A program with no
`import` keeps the v0.2 single-file model.

**Limitations.** Not in v0.3: aliases, `import *`, namespaces, packages,
`./foo`, `"math.echo"`, dynamic imports, re-export, cycle recovery.

**Priority.** Frozen.

**Possible version.** Done (v0.3). Do not start v0.4 module features here.

---

### Visibility

**What it means.** Public vs private names.

**Echo status.** Supported.

Nothing is exported by default. `export fn` / `export name: T = ...`
makes a name visible. Private names do not leak.

**Priority.** Frozen.

**Possible version.** Done (v0.3).

---

### Language errors

**What it means.** Failures are Echo diagnostics, not host-language junk.

**Echo status.** Partial.

Echo owns lex, parse, semantic, type, name, argument, index, mutation,
runtime, and module errors. Diagnostics include file, line, and column
when available. Python exceptions must not leak (tested).

User-level recovery for expected absence is inquiry + `*Or` (failure model).
There is still no catch-and-continue for arbitrary failures.

**Priority.** Later polish on messages/codes. Failure form is frozen.

**Possible version.** Diagnostics since v0.2; `*Or` in 0.5.3.

---

### `watch`

**What it means.** Observe a binding as it changes.

**Echo status.** Supported.

```echo
watch counter;
```

Reports assignment and mutating operations, including indexed assignment.

**Limitations.** Not a stepper. No breakpoints, `trace`, or `profile`.
Those are ecosystem / vision items.

**Priority.** Frozen as a fundamental. Richer observability is later.

**Possible version.** Done.

---

## 2. Language usability

Host, stdlib, and convenience. Most of the original v0.3 gaps shipped in 0.4–0.5;
0.6–0.7 filled collections and binding sugar. Remaining rows are called out below.

### Type conversion

**What it means.** Move between `int`, `float`, `str`, `bool` on purpose.

**Echo status.** Supported (`asIntOr` / `asFloatOr` in 0.5.3).

`asInt`, `asFloat`, `asBool`, `asString`, and `type` exist as methods and
standalone calls. Failed `asInt` / `asFloat` abort with Echo type errors.
`asIntOr` / `asFloatOr` return a fallback for unparseable strings, `null`,
lists, and hashes. `asInt(true)` / `asFloat(true)` stay type errors — bool has
no twin. There is no implicit `str + int`.

**Limitations.**

- No parsing options, base, or locale
- `asBool` follows truthiness

**Priority.** Frozen.

**Possible version.** Conversion corrected in 0.4; `*Or` in 0.5.3.

---

### File I/O

**What it means.** A program can read and write files.

**Echo status.** Supported (0.4+).

Builtins: `readFile` / `readFileOr`, `writeFile`, `fileExists`, `isDir`,
`listFiles`, `mkdir`, `removeFile`, `copyFile`, `cwd`, `pathJoin`. UTF-8 text
for read/write. Hosts may deny files (`E2801`); the playground does.

**Current syntax.** Standalone calls (not `file.read()` namespaces).

**Priority.** Frozen.

**Possible version.** 0.4 (twins in 0.5.3).

---

### User error handling

**What it means.** A program can represent and recover from expected failure.

**Echo status.** Partial. Failure model is frozen: abort by default; recovery is
inquiry (`fileExists`, `has`, `contains`, …) and `*Or` twins
(`envOr`, `readFileOr`, `parseJsonOr`, `asIntOr`, `asFloatOr`). See
`docs/failure-model.md`.

**Current syntax.** No `try` / `catch`, no `Result` / `Option`, no `?`.

**Limitations.** Expected absence is covered. Arbitrary catch-and-continue is
not. `echo test` continuing after `expect*` is runner-only.

**Priority.** Design hold. Do not add exceptions to “finish” this row.

**Possible version.** Form settled in the failure-model note; `*Or` in 0.5.3.

---

### Exceptions (`try/catch`)

**What it means.** Unwind the stack and resume in a handler.

**Echo status.** Excluded.

Held on purpose. Inquiry + `*Or` is the recovery surface. Do not copy
Python/JS `try` / `catch`.

**Priority.** Design hold.

**Possible version.** Hold.

---

### Destructuring

**What it means.** Unpack lists/hashes into names in one binding.

**Echo status.** Supported (0.7.1).

`[a: int, b: int] = pair;` and `{ id: int, name: str } = user;` unpack into names. Types are required on a fresh declaration. `[a, b] = pair;` assigns to existing names. List rest is last: `[head: int, rest: int...] = xs`. Hash rename: `{ id as userId: int }` (0.7.7). Hash rest: `{ id: int, rest: dynamic... }` (0.7.8). Same patterns in `fn` parameters. Missing hash keys abort. Extra hash keys go to rest when present; otherwise they are ignored.

**Current syntax.**

```echo
[a: int, b: int] = pair;
const [lo: int, hi: int] = bounds;
{ id: int, name: str } = user;
[head: int, rest: int...] = xs;
fn add([a: int, b: int]) -> int {
    return a + b;
}
```

**Limitations.** Nested hash patterns are not a dedicated form; nested list patterns work.

**Priority.** Done for 0.7.1.

**Possible version.** 0.7.1.

---

### Collection operations

**What it means.** Slice, map, filter, reduce, forEach, flatMap, flatten, some, every, findIndex, zip, unique, chunk, partition, rangeList, mapValues, contains, without handwritten loops.

**Echo status.** Supported through 0.6.9 HOFs; range expressions as values in 0.7.4.

Shipped: find, count, order, merge, clone, push/pull, keys/values/pairs,
`contains`, `slice()` / `xs[1:4]` (optional bounds 0.6.6), list `map` /
`filter` / `reduce` / `forEach` / `flatMap` / `some` / `every` / `findIndex` /
`zip` / `unique` / `chunk` / `flatten` / `partition`, `rangeList` /
`rangeListInclusive`, hash `mapValues` / `filter`, and range expressions
`0...10` / `0..10` (optional `by`) as `list` values (0.7.4).

**Priority.** Frozen for the shipped set. Further helpers are later polish.

**Possible version.** Through 0.6.9; range-as-value 0.7.4.

---

### String utilities

**What it means.** Split, replace, substring, contains, pad.

**Echo status.** Supported (0.4+).

Present: `trim`, `upperCase`, `lowerCase`, `length`, `reverse`, `format`,
interpolation, indexing, `split`, `replace` / `replaceFirst`, `contains`,
`slice` / slice syntax, `startsWith` / `endsWith`, `indexOf` / `lastIndexOf`,
`repeat`, `padStart` / `padEnd`, `join`.

**Limitations.** No regex. `format` is positional placeholders only.

**Priority.** Frozen.

**Possible version.** 0.4+.

---

### Date / time

**What it means.** Instants, durations, formatting, clocks.

**Echo status.** Missing (`now()` and `wait(seconds)` only).

No calendar, formatting, or duration type.

**Priority.** Later. Library, not syntax.

**Possible version.** Later.

---

### Environment variables

**What it means.** Read process environment.

**Echo status.** Supported (0.4).

`env(name)` aborts if unset (empty string counts as set). `envOr(name, fallback)`
returns the fallback when unset.

**Priority.** Frozen.

**Possible version.** 0.4.

---

### Program CLI arguments

**What it means.** The running program can see `argv` after the source path.

**Echo status.** Supported (0.4).

`args()` returns a new `list` of `str` — program arguments only, not the
source path and not `--plain`. CLI: interpreter flags, optional `--`, then
program arguments.

**Priority.** Frozen.

**Possible version.** 0.4.

---

### Default / variadic arguments

**What it means.** Optional parameters and `...rest`.

**Echo status.** Supported (0.6.0).

User `fn` parameters may have defaults (`punct: str = "!"`) and a
trailing variadic (`parts: int...`, bound as a list of `T`). Defaults
come before the variadic and are evaluated at call time when omitted.
Function types still spell parameter types only (`fn(int, str) -> int`).
As of 0.6.9 they honor trailing defaults on assignability: a value of
`fn(x: int, y: int = 0) -> int` matches `fn(int) -> int` and
`fn(int, int) -> int`, not `fn() -> int`. Variadics still have to match.
`say` / `eprint` / `format` / `pathJoin` stay variadic builtins.
Overloading stays held.

**Priority.** Frozen.

**Possible version.** 0.6.0.

---

### Function overloading

**What it means.** Same name, different signatures.

**Echo status.** Excluded.

Rejected in the v0.2 contract. Echo already has keyword arguments and
explicit types. Overloads would fight that simplicity.

**Priority.** Design hold.

**Possible version.** Hold.

---

### JSON / interchange

**What it means.** Read and write a common structured format.

**Echo status.** Supported (0.4); `parseJsonOr` in 0.5.3.

`parseJson` / `writeJson` convert between Echo values and JSON text.
`parseJsonOr(text, fallback)` returns the fallback on invalid JSON.

**Priority.** Frozen.

**Possible version.** 0.4 / 0.5.3.

---

### Multiline strings

**What it means.** Literals that span lines.

**Echo status.** Supported (0.5.0).

Triple-quoted `"""` / `'''` may span lines and still interpolate `${...}`.
Ordinary single-line quotes still reject a raw newline.

**Priority.** Frozen.

**Possible version.** 0.5.0.

---

## 3. Language ecosystem

Not language features. fmt / lint / test / check / REPL shipped; package
manager and LSP have not.

### Package manager

**Status.** Missing.

No Echo packages, lockfiles, or registries. `pyproject.toml` is for the
Python interpreter package.

**Priority.** Tooling track. Do not pretend this is v0.4 syntax.

**Possible version.** Tooling. Needs a module story beyond sibling files first.

---

### Formatter

**Status.** Implemented (0.5.4).

`echo fmt [paths...]` rewrites Echo sources in place. `--check` reports
dirty files without writing. Directory arguments recurse for `*.echo`.
Go’s `gofmt` is still the reference: one style, no layout knobs.

**Priority.** Tooling. Shipped.

**Possible version.** 0.5.4.

---

### Linter

**Status.** Implemented (0.5.5), expanded (0.5.8).

The semantic analyzer already rejects real mistakes. `echo lint` covers
style and convention: unused locals/functions/imports, comparison to
boolean literals, redundant `by 1`, empty if/function bodies, shadowed
builtins, `test-naming`, `self-assign`, and `unreachable-after-fail`.
It does not re-run typechecking. Unused parameters are `unused-local`.
`unused-export` and `redundant-parens` are not rules.

**Priority.** Tooling. Shipped.

**Possible version.** 0.5.8.

---

### Native test runner

**Status.** Implemented (0.5.6) as tooling. No new keywords.

`echo test [paths...]` discovers `*_test.echo` files in directories (explicit paths always run), calls zero-argument top-level `fn testXxx()` functions as separate units, and prints a pass/fail summary. `expect` / `expectEq` / `expectNeq` record and continue under the runner; `assert` / `fail` still abort the current unit. **0.6.8** adds `-run` / `--run` glob filter on those function unit names (not file names). **0.6.9** adds `--json` for a machine-readable report (totals, per-unit pass/fail, skipped from `-run`, failure message and location).

There is no `test "name" { }` syntax. That stays vision / held.

**Priority.** Tooling / vision. Shipped as a library-plus-CLI.

**Possible version.** 0.6.9 (`--json`).

---

### Debugger

**Status.** Partial.

`watch` is real. There is no stepper, breakpoints, or stack inspector.

**Priority.** Tooling. Do not build a VM to get a debugger.

**Possible version.** Later.

---

### Documentation generator

**Status.** Missing.

VitePress documents the language for humans. There is no docstring
extract / API generator for Echo modules.

**Priority.** Later.

**Possible version.** Later. Needs richer modules first.

---

### IDE support

**Status.** Partial (0.5.7). Check workspace in 0.5.9. Not an LSP.

`echo-syntax-highlighter/` is a VS Code / Cursor extension: TextMate grammar
(also imported by the docs site for Echo code fences), task provider, and
problem matchers. It highlights current keywords, types, builtins (`expect`,
`fail`, `assert`, `*Or` twins, host/stdlib), comments, strings with `${...}`,
and number literals.

Commands / Run Task run `echolang check`, `fmt`, `lint`, and `test` (`--plain`)
so CLI diagnostics appear in the Problems panel. **Echo: Check workspace**
(0.5.9) runs `echolang check --plain` on the folder; **Echo: Check file**
remains. Format Document shells out to `echolang fmt`. There are still no
completions, jump-to-definition, or a language server.

**Priority.** Tooling. Shipped as highlight + tasks.

**Possible version.** 0.5.9.

---

### Language server

**Status.** Missing.

**Priority.** Later. Worth more after the analyzer is treated as a
public API.

**Possible version.** Later.

---

### REPL

**Status.** Supported (0.5.0).

`echo` with no source file starts a REPL. Bindings persist for the process.
Continuation spans braces and unterminated triple-quoted strings. Failed
submissions return to the prompt. `--plain` works. `import` loads sibling
`.echo` files from the working directory. `echo check` (0.4.1; multi-path
0.5.9) is separate analysis tooling.

**Priority.** Tooling. Shipped.

**Possible version.** 0.5.0.

---

### Playground

**Status.** Partial.

Docs-site browser runner. Restricted host (no files, no `run`). Complements
the CLI REPL; does not replace it.

**Priority.** Tooling. Good enough for now.

**Possible version.** Done enough.

---

## 4. Implementation / runtime maturity

Held. Empty cells here are not near-term work.

| Capability | Status | Why not now |
| --- | --- | --- |
| Compiler / native executable | Missing | Python tree-walk is a strategic choice |
| Bytecode / VM | Missing | Strategic hold; not the near-term bottleneck |
| JIT | Missing | Same |
| Concurrency / async | Missing | Vision mentions orchestration later. Not a v0.4 language hole |
| Generics | Missing | Premature type-theory |
| Classes / OOP | Supported (0.8.6) | Classes + `new { }` fields/defaults + bound/unbound/type methods + interfaces; no inheritance |
| Structs / records | Partial | Type aliases, exact shapes, and class fields |
| Garbage collection | Partial | Python owns GC. Echo does not need its own |

`docs/language-semantics.md` already says there is no bytecode VM in v0.2.
v0.3 did not add one. That remains correct.

---

## Echo vs reference languages

Capability comparison only. Echo is not trying to become these languages.

### Python

| Capability | Status for Echo |
| --- | --- |
| First-class functions / lambdas | Shipped (0.6.0); builtins as values (0.7.3) |
| Exceptions | Excluded; inquiry + `*Or` instead |
| File / OS / env / argv | Shipped (0.4+) |
| REPL | Shipped (0.5.0) |
| Packages (pip) | Missing. Sibling-file modules only |
| Classes | Supported (0.8.6; no inheritance) |
| Default args, variadics, slices | Shipped (0.6.x); no comprehensions |

### JavaScript

| Capability | Status for Echo |
| --- | --- |
| Functions as values | Shipped |
| `try/catch` | Excluded |
| Promises / async | Don’t touch |
| JSON | Shipped (0.4+) |
| Objects as records | Hashes + aliases / exact |
| Modules | Smaller sibling-file system; shipped |
| Class / prototype OOP | Excluded |

### Go

| Capability | Status for Echo |
| --- | --- |
| Compile-time types | Decision: runtime-checked |
| Structs | Partial via aliases / exact |
| Explicit errors | Closest taste: abort + `*Or` |
| Packages | Sibling files only |
| `gofmt` / `go test` | Echo has `fmt` / `test` |
| Goroutines | Don’t touch |

### Rust

| Capability | Status for Echo |
| --- | --- |
| Ownership / borrow checker | Out of scope |
| `Result` / `Option` | Not types; `*Or` + inquiry cover absence |
| Traits / generics | Don’t touch |
| Pattern matching | Destructuring + `switch` (0.7.6); no `match` / `Result` form |
| Cargo | Missing |

---

## Genuine holes vs things we do not want

### Still open (usability / ecosystem)

1. Date / time library (beyond `now` / `wait`)
2. Package manager / non-sibling module paths
3. Language server / richer editor support
4. Optional sugar still held where listed in priority

### Shipped that used to be holes

args, env, files, JSON, string/collection helpers, conversion, failure-model
`*Or` twins, formatter, test runner, REPL, first-class functions, `const`,
destructuring, exact objects, unions, range-as-value, nominal classes (0.8.0), methods + `this` (0.8.1), interfaces (0.8.2), `new { ... }` fields (0.8.3), field defaults (0.8.4), unbound methods (0.8.5), type methods (0.8.6).

### Not holes (held)

- Overloading
- Generics; class inheritance
- Bytecode, VM, JIT, native compile
- Concurrency
- `try/catch`

### Echo already has that references often add later

- `watch`
- Explicit outer mutation (`use` / `use mut`)
- Categorized diagnostics
- Modules with private-by-default exports

---

## What not to do next

Do not treat empty cells as a queue. Do not add a VM, generics, inheritance, or
`try/catch` because a checklist looks incomplete. Do not weaken Model A.
This file is not a contract — semantics, modules, and the failure model win.

v0.4 was host + stdlib ([archive/v0.4-language-vs-stdlib](/archive/v0.4-language-vs-stdlib)). Later releases
added syntax and tooling; see `CHANGELOG.md` through **0.8.6**.

---

## Evidence

Judged from:

- `docs/language-semantics.md`
- `docs/module-semantics.md`
- `docs/failure-model.md`
- `docs/standard-library/built-in-methods.md`
- `CHANGELOG.md`
- `src/echo/` and `tests/`

Ignore as evidence: pre-architecture audits and any doc that still claims
args/env/files/JSON/REPL are missing.
