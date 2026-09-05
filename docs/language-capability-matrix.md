# Echo Language Capability Matrix

**Status:** Design audit after v0.3.0. Not a language contract.
**Language contracts remain:** `docs/language-semantics.md` (v0.2) and `docs/module-semantics.md` (v0.3, frozen).
**Date:** 2026-09-05

This document is **not** a promise list and **not** a v0.4 specification.
v0.3 language semantics stay frozen. Nothing here authorizes syntax or
runtime changes until an explicit language revision.

---

## Why this exists

Echo now has a real pipeline: frontend → semantics → modules → runtime.
That is the first point where a fundamentals audit is useful.

The question is not “does Python have X?”
The question is:

> What capability would a usable general-purpose scripting language
> need, what does Echo actually have, and is a gap a hole or a decision?

---

## How to read a row

| Field | Meaning |
| --- | --- |
| **Status** | Current implementation, judged against the contracts and `src/echo/` |
| **Supported** | End-to-end: syntax, semantics, runtime, and tests |
| **Partial** | Present, but incomplete for real programs |
| **Missing** | Not in the language or stdlib today |
| **Excluded** | Absent on purpose. The contract or vision rejects it, or confines it to a special case |
| **Priority** | Whether we should care soon. “Don’t touch” means leave it alone |
| **Possible version** | A guess, not a commitment |

`Candidate` is a recommendation, not a status.
A missing capability can be a candidate. An excluded one can be a
reconsideration. Those are different things.

---

## Snapshot after v0.3.0

Echo is already a language in the fundamentals sense.

It has typed bindings, expressions, operators, control flow, loops,
functions, lexical scope, closures, collections, strings, an explicit
mutability model, modules with visibility, and Echo-owned errors.

It is **not** yet a pleasant host for real automation programs.
The first interesting gaps are usability: conversion, I/O, program
arguments, richer collections/strings, and a designed failure story.

It is **not** unfinished because it lacks a VM, generics, or classes.

| Bucket | Verdict |
| --- | --- |
| Language fundamentals | Surprisingly complete for v0.3 |
| Language usability | First real gaps |
| Language ecosystem | Thin. Expected at this age |
| Implementation / runtime maturity | Do not start |

Distinctive Echo capabilities that are not “missing Python features”:

- `watch` as a language construct
- `use` / `use mut` instead of implicit outer mutation
- runtime-checked declarations without a static compiler
- `import` / `export` kept separate from `use`
- Model A: imported bindings are immutable; imported collections share identity

---

## Summary

| Capability | Bucket | Status | Priority | Possible version |
| --- | --- | --- | --- | --- |
| Variables | Fundamentals | Supported | Frozen | Done (v0.2) |
| Immutable bindings | Fundamentals | Partial | Later | v0.4+ if wanted |
| Primitive types | Fundamentals | Supported | Frozen | Done |
| Type checking | Fundamentals | Supported | Frozen | Done |
| Type aliases | Fundamentals | Partial | Later | Later |
| Arithmetic | Fundamentals | Supported | Frozen | Done |
| Comparisons | Fundamentals | Supported | Frozen | Done |
| Boolean logic | Fundamentals | Supported | Frozen | Done |
| Strings | Fundamentals | Supported | Frozen | Done |
| Lists | Fundamentals | Supported | Frozen | Done |
| Hashes | Fundamentals | Supported | Frozen | Done |
| Indexing | Fundamentals | Supported | Frozen | Done |
| Control flow | Fundamentals | Supported | Frozen | Done |
| Loops | Fundamentals | Supported | Frozen | Done |
| Loop control | Fundamentals | Supported | Frozen | Done |
| Functions | Fundamentals | Supported | Frozen | Done |
| Recursion | Fundamentals | Partial | Later | Later |
| Closures | Fundamentals | Supported | Frozen | Done |
| First-class functions | Fundamentals | Excluded | Design hold | v0.4+ reconsideration |
| Scope | Fundamentals | Supported | Frozen | Done |
| Mutation (`use` / `use mut`) | Fundamentals | Supported | Frozen | Done |
| Modules | Fundamentals | Supported | Frozen | Done (v0.3) |
| Visibility | Fundamentals | Supported | Frozen | Done (v0.3) |
| Language errors | Fundamentals | Partial | Usability now | v0.4 candidate |
| `watch` | Fundamentals | Supported | Frozen | Done |
| Type conversion | Usability | Partial | Usability now | v0.4 candidate |
| File I/O | Usability | Missing | Usability now | v0.4 candidate (library) |
| User error handling | Usability | Missing | Usability now | v0.4+ (form undecided) |
| Exceptions (`try/catch`) | Usability | Missing | Design hold | Reconsider form, do not copy |
| Destructuring | Usability | Missing | Later | Later |
| Collection operations | Usability | Partial | Usability now | v0.4 candidate |
| String utilities | Usability | Partial | Usability now | v0.4 candidate |
| Date / time | Usability | Missing | Later | Later (library) |
| Environment variables | Usability | Missing | Usability now | v0.4 candidate (library) |
| Program CLI arguments | Usability | Missing | Usability now | v0.4 candidate |
| Default / variadic args | Usability | Excluded | Design hold | Later reconsideration |
| Function overloading | Usability | Excluded | Design hold | Hold |
| JSON / interchange | Usability | Missing | Usability now | v0.4 candidate (library) |
| Multiline strings | Usability | Missing | Later | Later |
| Package manager | Ecosystem | Missing | Tooling | Tooling track |
| Formatter | Ecosystem | Missing | Tooling | Tooling track |
| Linter | Ecosystem | Missing | Tooling | Tooling track |
| Native test runner | Ecosystem | Missing | Tooling | Tooling / vision |
| Debugger | Ecosystem | Partial | Tooling | Later |
| Documentation generator | Ecosystem | Missing | Tooling | Later |
| IDE support | Ecosystem | Partial | Tooling | Tooling track |
| Language server | Ecosystem | Missing | Tooling | Later |
| REPL | Ecosystem | Missing | Tooling | Later (`echo check` / REPL) |
| Playground | Ecosystem | Partial | Tooling | Done enough |
| Compiler / native exe | Runtime | Missing | Don't touch | Not now |
| Bytecode / VM | Runtime | Missing | Don't touch | Not now |
| JIT | Runtime | Missing | Don't touch | Not now |
| Concurrency / async | Runtime | Missing | Don't touch | Not now |
| Generics | Runtime | Missing | Don't touch | Not now |
| Classes / OOP | Runtime | Excluded | Design hold | Hold |
| Structs / records | Runtime | Partial | Later | Later |
| Garbage collection | Runtime | Partial | Don't touch | Python-owned |

---

## 1. Language fundamentals

These decide whether Echo is a language.

### Variables

**What it means.** Introduce a name, give it a type, assign, reassign.

**Why languages need it.** Every program stores values.

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

**Why languages need it.** Stops accidental overwrites. Makes APIs safer.

**Echo status.** Partial.

Echo has no `const` declaration. Bindings are mutable in the declaring
scope. Reassignment can be blocked in two other places:

- `use name;` inside a function is read-only
- imported module bindings are immutable (v0.3 Model A)

**Current syntax.**

```echo
fn read_only() {
    use count;
    // count = 1;   // mutation error
}
```

**Limitations.** You cannot declare a module-level constant. Immutability
is a scope/import property, not a declaration form.

**Priority.** Later. Not a fundamentals hole.

**Possible version.** v0.4+ if a `const` form is wanted. Do not invent one
just to fill this cell.

---

### Primitive types

**What it means.** A small set of first-class values.

**Why languages need it.** Programs need numbers, text, booleans, and absence.

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

**Why languages need it.** Catches the wrong value at a known boundary.

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

**Why languages need it.** Lets programs talk about `User` instead of a raw hash.

**Echo status.** Partial.

```echo
type Age = int;
type User = { id: int, name: str };
```

Object aliases require the listed fields and types. Extra fields are
allowed. Aliases are not new runtime types.

**Limitations.** No exact-shape option, no nominal types, no methods on
aliases. This is the closest thing Echo has to records.

**Priority.** Later.

**Possible version.** Later (exact object validation is already on the
short roadmap).

---

### Arithmetic

**What it means.** `+ - * / %` and unary `-`.

**Why languages need it.** Numeric programs.

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

**Why languages need it.** Conditions and ordering.

**Echo status.** Supported.

`true == 1` is `false`. `null == null` is `true`. Lists and hashes compare
structurally.

**Priority.** Frozen.

**Possible version.** Done.

---

### Boolean logic

**What it means.** Conjunction, disjunction, negation, with defined truthiness.

**Why languages need it.** Control flow.

**Echo status.** Supported.

Operators: `&&`, `||`, `!`. They short-circuit. Falsy values: `false`,
`null`, `0`, `0.0`, `""`, `[]`, `{}`.

**Limitations.** No `and` / `or` / `not` keywords. That is spelling, not a hole.

**Priority.** Frozen.

**Possible version.** Done.

---

### Strings

**What it means.** Create, concatenate, interpolate.

**Why languages need it.** Almost every script prints or builds text.

**Echo status.** Supported.

Quotes: `"..."` and `'...'`. Interpolation `${expression}` works in both.
Escapes: `\\`, `\"`, `\'`, `\n`, `\t`, `\r`.

**Limitations.** Strings are single-line. A newline inside quotes is a
lex error. No raw / multiline literal.

**Priority.** Frozen as a fundamental. Multiline is a usability item.

**Possible version.** Done.

---

### Lists

**What it means.** Ordered mutable sequence: create, access, modify.

**Why languages need it.** Sequences are the default data structure.

**Echo status.** Supported.

Built-ins include `push`, `insertAt`, `pull`, `removeValue`, `empty`,
`find`, `countOf`, `order`, `clone`, `merge`, `reverse`, `length`.

**Limitations.** `clone()` is shallow. No slice syntax. `order(comparator)`
is the only place a function may be referred to by name as a value.
`removeValue` errors if the value is missing (contract); some older docs
still say it is a no-op.

**Priority.** Frozen.

**Possible version.** Done.

---

### Hashes

**What it means.** String-key maps: create, access, modify.

**Why languages need it.** Records, configs, counters, grouped data.

**Echo status.** Supported.

Built-ins include `keys`, `values`, `pairs`, `ensure`, `take`,
`take_last`, `wipe`, `merge`, `clone`.

**Limitations.** Runtime indexing keys must be `str`. No int keys, no
nested-path syntax.

**Priority.** Frozen.

**Possible version.** Done.

---

### Indexing

**What it means.** `list[0]`, `map["x"]`, nested assignment.

**Why languages need it.** Collections are unused without access.

**Echo status.** Supported.

List indexes are `int` in `[0, length)`. Hash keys in `[]` must be `str`.
Out-of-range and missing keys are Echo errors. Indexed assignment follows
`use mut` rules.

**Priority.** Frozen.

**Possible version.** Done.

---

### Control flow

**What it means.** Conditional execution.

**Why languages need it.** Programs branch.

**Echo status.** Supported.

`if`, `else`, `else if`. Conditions use truthiness. Blocks are scoped.

**Limitations.** No `switch` / `match`. Not a fundamentals hole.

**Priority.** Frozen.

**Possible version.** Done.

---

### Loops

**What it means.** Repeat work.

**Why languages need it.** Collections and numeric ranges.

**Echo status.** Supported.

- `while cond { }`
- `for i: int in start..end by step { }` — `..` inclusive, `...` exclusive
- `foreach item: T in iterable { }` — `list` or `hash` (keys as `str`)

`by 0` is a runtime error. Non-numeric bounds are not convertible.

**Limitations.** No iterator protocol beyond lists/hashes. No infinite
`loop` keyword.

**Priority.** Frozen.

**Possible version.** Done.

---

### Loop control

**What it means.** `break` and `continue`.

**Why languages need it.** Exit or skip without extra flags.

**Echo status.** Supported.

Both are only valid inside loops. The analyzer rejects them elsewhere.

**Limitations.** No labeled break. No `break value`. Those are extras,
not the basic expectation.

**Priority.** Frozen.

**Possible version.** Done.

The earlier “partial” instinct was wrong. The basic capability is present.

---

### Functions

**What it means.** Named callable with parameters and return values.

**Why languages need it.** Abstraction.

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

**Limitations.** No default arguments, variadics, or overloads. That is
the v0.2 contract, not an accident.

**Priority.** Frozen.

**Possible version.** Done.

---

### Recursion

**What it means.** A function may call itself.

**Why languages need it.** Trees, divide-and-conquer, some algorithms.

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

**Why languages need it.** Callbacks, helpers, lexical state.

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

**Why languages need it.** Higher-order APIs, callbacks, `map`/`filter`.

**Echo status.** Excluded.

Echo currently:

- supports functions
- supports closures
- supports a named function reference in `order(comparator)`
- does **not** generally treat functions as values in source syntax

This is in `docs/language-semantics.md`. It is not accidentally missing.

```echo
// legal special case
nums.order(descending);

// not a general function value
// fn makeCounter() { ... return bump; }
```

**Limitations.** You cannot store a function in a list, return one, or
pass one except to `order`.

**Priority.** Design hold.

**Possible version.** v0.4+ reconsideration. Reopening this is a language
change, not a bugfix.

---

### Scope

**What it means.** Predictable name resolution.

**Why languages need it.** Without this, nothing else is trustworthy.

**Echo status.** Supported.

Lexical scoping. Innermost enclosing declaration at the definition site.
`if` / `else` / `while` / `for` / `foreach` create block scopes.
Function scope parent is the closure. User declarations may shadow builtins.

**Priority.** Frozen.

**Possible version.** Done.

---

### Mutation (`use` / `use mut`)

**What it means.** Outer writes are explicit.

**Why languages need it.** Hidden mutation is how scripting languages
become undebuggable.

**Echo status.** Supported. This is an Echo differentiator.

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

**Why languages need it.** One file is a sketch. Real programs need
boundaries.

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

**Why languages need it.** Accidental API surface is a design bug.

**Echo status.** Supported.

Nothing is exported by default. `export fn` / `export name: T = ...`
makes a name visible. Private names do not leak.

**Priority.** Frozen.

**Possible version.** Done (v0.3).

---

### Language errors

**What it means.** Failures are Echo diagnostics, not host-language junk.

**Why languages need it.** A language that prints `ValueError` is not
finished.

**Echo status.** Partial.

Echo owns lex, parse, semantic, type, name, argument, index, mutation,
runtime, and module errors. Diagnostics include file, line, and column
when available. Python exceptions must not leak (tested).

What is missing is **user-level** handling: a program cannot catch,
recover, or return a structured failure. Errors abort.

**Current syntax.** None for the user. Failures come from the language.

**Priority.** Usability now — but the *form* is a design problem, not
“add `try/catch`”.

**Possible version.** v0.4 candidate for a designed failure model.

---

### `watch`

**What it means.** Observe a binding as it changes.

**Why languages need it.** Most languages bolt debugging on later.
Echo can make observability part of the language.

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

These decide whether writing a real program is pleasant.
This is where the first interesting gaps are.

### Type conversion

**What it means.** Move between `int`, `float`, `str`, `bool` on purpose.

**Why languages need it.** Input is strings. Arithmetic is numbers.

**Echo status.** Partial.

`asInt`, `asFloat`, `asBool`, `asString`, and `type` exist as methods
and standalone calls. Failed `asInt` / `asFloat` raise Echo type errors.
There is no implicit `str + int`.

**Limitations.**

- No `asInt` error that distinguishes “not a number” from overflow
- `asBool` follows truthiness, including `bool` from `0` / `""` / `[]`
- `asInt(true)` becomes `1` even though `bool` is not an `int`
- No parsing options, no base, no locale

**Priority.** Usability now.

**Possible version.** v0.4 candidate (tighten rules and errors, not new syntax).

---

### File I/O

**What it means.** A program can read and write files.

**Why languages need it.** Scripts that cannot touch a file stay demos.

**Echo status.** Missing.

The CLI reads a `.echo` source file. Echo programs have no `file.read`
or `file.write`. Vision says filesystem utilities belong in a library,
not the parser.

**Current syntax.** None.

**Priority.** Usability now, as a **library**, not new syntax.

**Possible version.** v0.4 candidate.

---

### User error handling

**What it means.** A program can represent and recover from expected failure.

**Why languages need it.** Networks fail. Files are missing. Input is bad.
Abort-only languages force every caller to hope.

**Echo status.** Missing.

**Current syntax.** None.

**Limitations.** This is not the same as diagnostics. Echo already explains
failures well for the *implementers* of Echo. User programs cannot handle
them.

**Priority.** Usability now. Design the model before adding syntax.

**Possible version.** v0.4+. Candidates include explicit result values,
not necessarily exceptions.

---

### Exceptions (`try/catch`)

**What it means.** Unwind the stack and resume in a handler.

**Why some languages need it.** It is one failure model. It is not the only one.

**Echo status.** Missing.

There is no written exclusion in the contract, unlike first-class
functions. There is also no reason to copy Python or JavaScript here.
Go’s `error` values and Rust’s `Result` are closer to Echo’s “explicit”
taste than `try/catch`.

**Priority.** Design hold. Do not add `try/catch` just because the cell is empty.

**Possible version.** Reconsider with user error handling, as one possible form.

---

### Destructuring

**What it means.** Unpack lists/hashes into names in one binding.

**Why languages need it.** Convenience. Rarely a semantic necessity.

**Echo status.** Missing.

**Priority.** Later. Sugar.

**Possible version.** Later.

---

### Collection operations

**What it means.** Slice, map, filter, reduce, contains, without handwritten loops.

**Why languages need it.** Real scripts spend most of their time on collections.

**Echo status.** Partial.

Echo already has find, count, order, merge, clone, push/pull, keys/values/pairs.
It does not have slices, map/filter, or `contains` as a primitive.

Higher-order helpers collide with the first-class-function hold.
Any `map`/`filter` design has to face that decision.

**Priority.** Usability now for non-higher-order helpers (`contains`,
slice, maybe `join`). Hold `map`/`filter` until functions-as-values is reopened.

**Possible version.** v0.4 candidate for the non-HOF set.

---

### String utilities

**What it means.** Split, replace, substring, contains, pad.

**Why languages need it.** Automation is mostly text.

**Echo status.** Partial.

Present: `trim`, `upperCase`, `lowerCase`, `length`, `reverse`, `format`,
interpolation, indexing.

Missing: `split`, `replace`, `contains`, substring/slice, starts/ends with,
character iteration helpers.

**Priority.** Usability now.

**Possible version.** v0.4 candidate (stdlib methods, not syntax).

---

### Date / time

**What it means.** Instants, durations, formatting, clocks.

**Why languages need it.** Logs, schedules, timeouts, timestamps.

**Echo status.** Missing.

`wait(seconds)` sleeps. That is not a time library.

**Priority.** Later. Library, not syntax.

**Possible version.** Later.

---

### Environment variables

**What it means.** Read process environment.

**Why languages need it.** Secrets, config, CI, automation hosts.

**Echo status.** Missing.

**Priority.** Usability now. Library.

**Possible version.** v0.4 candidate.

---

### Program CLI arguments

**What it means.** The running program can see `argv` after the source path.

**Why languages need it.** `echo app.echo -- input.txt` is how scripts start.

**Echo status.** Missing.

The Echo CLI accepts `source`, `--plain`, and `--version`. Those flags
are for the interpreter, not the program.

**Priority.** Usability now.

**Possible version.** v0.4 candidate.

---

### Default / variadic arguments

**What it means.** Optional parameters and `...rest`.

**Why languages need it.** Convenience at API boundaries.

**Echo status.** Excluded.

The v0.2 contract: no default arguments, variadics, or overloads.
`say` and `format` are variadic built-ins only.

**Priority.** Design hold.

**Possible version.** Later reconsideration.

---

### Function overloading

**What it means.** Same name, different signatures.

**Why some languages need it.** Ad-hoc polymorphism.

**Echo status.** Excluded.

Rejected in the v0.2 contract. Echo already has keyword arguments and
explicit types. Overloads would fight that simplicity.

**Priority.** Design hold.

**Possible version.** Hold.

---

### JSON / interchange

**What it means.** Read and write a common structured format.

**Why languages need it.** Automation talks to other tools.

**Echo status.** Missing.

Hashes are in-memory only. No `json.parse` / `json.write`.

**Priority.** Usability now. Library.

**Possible version.** v0.4 candidate.

---

### Multiline strings

**What it means.** Literals that span lines.

**Why languages need it.** Embedded SQL, HTML, long messages, fixtures.

**Echo status.** Missing.

A newline inside quotes is a lex error. You can concatenate or use `\n`.

**Priority.** Later.

**Possible version.** Later.

---

## 3. Language ecosystem

These are not language features. A language without them still feels
unfinished quickly. Echo already has a docs site, a playground, a
TextMate grammar, and pytest for the **implementation**.

### Package manager

**Status.** Missing.

No Echo packages, lockfiles, or registries. `pyproject.toml` is for the
Python interpreter package.

**Priority.** Tooling track. Do not pretend this is v0.4 syntax.

**Possible version.** Tooling. Needs a module story beyond sibling files first.

---

### Formatter

**Status.** Missing.

No canonical `echo fmt`. Go’s `gofmt` is the reference for leverage:
one style, no arguments.

**Priority.** Tooling. High value, no language change.

**Possible version.** Tooling track.

---

### Linter

**Status.** Missing.

The semantic analyzer already rejects real mistakes. A linter would
cover style and smells (`use` unused, shadowed names, etc.).

**Priority.** Tooling. After or with a formatter.

**Possible version.** Tooling track.

---

### Native test runner

**Status.** Missing as a language product.

The repo has a serious pytest suite for Echo itself (341 passed, 2
xfailed at the v0.3.0 collection fix). That tests the interpreter.
There is no `echo test` and no `test "name" { }` syntax.

Vision wants a native testing story. That can start as a library plus
CLI, without new keywords.

**Priority.** Tooling / vision. High identity fit.

**Possible version.** Tooling first; syntax only if the library is not enough.

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

**Status.** Partial.

`echo-syntax-highlighter/` is a VS Code TextMate grammar. No completions,
no jump-to-definition, no diagnostics in the editor.

**Priority.** Tooling.

**Possible version.** Tooling track.

---

### Language server

**Status.** Missing.

**Priority.** Later. Worth more after the analyzer is treated as a
public API.

**Possible version.** Later.

---

### REPL

**Status.** Missing.

`echo` without a file prints help and exits. The docs playground runs
programs in the browser. That is not a REPL.

Roadmap already lists “REPL and `echo check`”.

**Priority.** Tooling.

**Possible version.** Later.

---

### Playground

**Status.** Partial.

The docs site can run Echo in the browser. It is the closest thing to
interactive execution. It is not a substitute for a CLI REPL, and it
is not a full host (no files, no argv).

**Priority.** Tooling. Good enough for now.

**Possible version.** Done enough.

---

## 4. Implementation / runtime maturity

Do not touch these because they appear on a checklist.

| Capability | Status | Why not now |
| --- | --- | --- |
| Compiler / native executable | Missing | Python tree-walk is a strategic choice |
| Bytecode / VM | Missing | Current bottleneck is language and usability |
| JIT | Missing | Same |
| Concurrency / async | Missing | Vision mentions orchestration later. Not a v0.4 language hole |
| Generics | Missing | Premature type-theory |
| Classes / OOP | Excluded | Hashes + aliases cover data. Vision: do not become a smaller Python |
| Structs / records | Partial | Type aliases already name shapes |
| Garbage collection | Partial | Python owns GC. Echo does not need its own |

`docs/language-semantics.md` already says there is no bytecode VM in v0.2.
v0.3 did not add one. That remains correct.

---

## Echo vs reference languages

Compared only for **fundamental capabilities**, not ecosystems or speed.
Echo should not become any of these languages.

### Python — simplicity / dynamic language

What Python gives you that Echo does not:

| Capability | Hole or decision? |
| --- | --- |
| First-class functions and lambdas | Decision. Excluded. |
| Exceptions | Missing failure model. Do not copy blindly. |
| File / OS / env / argv | Genuine usability hole. |
| REPL | Ecosystem hole. |
| Packages (pip) | Ecosystem. Echo modules are sibling files. |
| Classes | Decision. Keep out of core. |
| Default args, `*args`, slices, comprehensions | Mix of exclusion and sugar. |

Python lesson: Echo does not need to be more dynamic.
It needs the **script host** pieces Python users forget are not “language”:
files, arguments, environment, a way to run interactively.

### JavaScript — scripting language

| Capability | Hole or decision? |
| --- | --- |
| Functions as values | Decision. |
| `try/catch` | Same as Python. Form undecided. |
| Promises / async | Runtime. Don’t touch. |
| JSON | Genuine usability hole (library). |
| Objects as records | Echo hashes + type aliases already cover the basic need. |
| Modules | Echo has a smaller, stricter system. Not a hole. |
| Prototype / class OOP | Decision. Keep out. |

JavaScript lesson: first-class functions and async are how JS became a
platform. Echo’s identity is observability and explicit mutation, not
callback soup.

### Go — simple systems language

| Capability | Hole or decision? |
| --- | --- |
| Compile-time types | Decision. Echo is runtime-checked on purpose. |
| Structs | Partial via aliases. Not required to copy. |
| Multiple return / `error` values | Interesting **alternative** to exceptions. |
| Packages | Echo v0.3 is sibling files only. |
| `gofmt`, `go test` | Ecosystem lesson. Highest leverage tooling. |
| Goroutines | Runtime. Don’t touch. |

Go lesson: Echo should steal **taste**, not features. Small language,
explicit errors, one formatter, an official test command.

### Rust — strong type / system language

| Capability | Hole or decision? |
| --- | --- |
| Static safety, ownership | Out of scope. Don’t touch. |
| `Result` / `Option` | Interesting failure/absence model. |
| Traits / generics | Don’t touch. |
| Pattern matching | Later sugar, not a fundamental hole. |
| Cargo | Ecosystem. Same as packages. |

Rust lesson: absence and failure can be values. That fits Echo better
than stack-unwinding exceptions. It does **not** mean borrow checking.

---

## Genuine holes vs things we do not want

### Genuine holes (usability)

These block “write a real automation script” without changing Echo’s identity:

1. Program arguments
2. Environment variables
3. File I/O (library)
4. JSON (library)
5. String split / replace / contains / slice
6. Collection contains / slice (not `map`/`filter`)
7. Tighter type conversion
8. A designed user-level failure model

### Ecosystem holes (feel unfinished, not language bugs)

1. Formatter
2. Official test command (library + CLI first)
3. REPL / `echo check`
4. Richer editor support

### Not holes

- First-class functions
- Overloading
- Default / variadic user functions
- Classes
- Generics
- Bytecode, VM, JIT, native compile
- Concurrency
- `try/catch` copied from JavaScript

### Echo already has that the references often add later

- `watch`
- Explicit outer mutation
- Honest, categorized diagnostics
- Modules with private-by-default exports

---

## What not to do next

Do not open v0.4 by implementing this matrix top to bottom.
Do not add a VM, generics, classes, or `try/catch` because a cell is empty.
Do not weaken Model A or the two xfailed Model B tests.
Do not treat this file as a contract. If it disagrees with
`docs/language-semantics.md` or `docs/module-semantics.md`, those win.

The useful next conversation is only:

> Which usability holes are worth a v0.4 language revision,
> and which belong in a standard library with no new syntax?

---

## Evidence

Judged from:

- `docs/language-semantics.md`
- `docs/module-semantics.md`
- `docs/standard-library/built-in-methods.md`
- `src/echo/` (frontend, semantics, modules, runtime, CLI)
- `tests/` including `tests/modules/`

Stale on purpose and **not** used as evidence:

- `Echo-Technical-Audit.md` (pre-architecture snapshot)
- `docs/errors-diagnostics/known-limitations.md` still says there is no module system
- `docs/reference/cli-and-execution-model.md` still describes the v0.2 single-file CLI
