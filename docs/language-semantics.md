# Echo Language Semantics (v0.2)

This document is the contract for Echo v0.2. Implementation and tests must match it.
If code and this document disagree, the document is wrong only after an explicit language change.

Echo is an **interpreted, statement-based scripting language**.
Types are **declared explicitly and checked at runtime**. Echo is not statically typed.

---

## Values

Echo values are:

| Echo type | Meaning |
| --- | --- |
| `int` | Arbitrary-precision integer (not a fixed 32-bit width) |
| `float` | IEEE-754 binary64 floating-point number |
| `str` | Unicode text |
| `bool` | `true` or `false` |
| `null` | Absence of a value |
| `list` | Mutable ordered sequence |
| `hash` | Mutable string-key map |
| function | Named function value with a lexical closure |

`bool` is **not** a subtype of `int`. `true` is not a valid `int`.

`null` is a value. It is never the same as “this name does not exist.”

---

## Types

### Declarations

Variables are introduced with a type:

```echo
name: str = "Echo";
```

Reassignment does not repeat the type:

```echo
name = "Echo 2";
```

`void` is only valid as a function return annotation.

`dynamic` accepts any Echo value, including `null`.

### Type aliases

```echo
type Age = int;
type User = { id: int, name: str };
type ExactUser = exact { id: int, name: str };
```

Aliases are names for existing types. They are not new runtime types.
Open object aliases require the listed fields and field types while allowing extras.
Exact object types require every listed field and reject extras. Exactness nests,
does not freeze the hash, and may also be written inline. An exact type is
assignable to a compatible open type; an open type is not assignable to an exact type.

### Runtime checks

Echo checks types when:

- a variable is declared
- a variable is reassigned
- a function argument is bound
- an annotated function returns
- a `foreach` item is bound

Unknown type names are errors, not silent success.

---

## Null

```echo
x: dynamic = null;
say(x);   // null
```

Looking up `x` after this assignment yields `null`.
It must not fall through to a parent scope.

---

## Truthiness

Used by `if`, `while`, `&&`, `||`, `!`, and `default()`.

Falsy values: `false`, `null`, `0`, `0.0`, `""`, `[]`, `{}`.
Every other value is truthy.

---

## Equality

`==` and `!=` compare Echo values.

- `true == 1` is `false`
- `null == null` is `true`
- lists and hashes compare structurally

---

## Arithmetic

Operators: `+`, `-`, `*`, `/`, `%`, unary `-`.

- `int / int` truncates toward zero and returns `int`
- any other `/` is float division
- `int % int` uses the same toward-zero quotient
- division or modulo by zero is a runtime error
- `"a" + "b"` concatenates
- `[1] + [2]` concatenates lists
- mixed `str + int` is a type error, not a Python error

Compound assignment: `+=`, `-=`, `*=`, `/=`, `%=`.
`x += y` means `x = x + y` with the same type and mutability rules.

---

## Assignment

- A name must be declared before it is assigned.
- Redeclaring the same name in the same scope is an error.
- A child block may shadow a parent declaration.
- Indexed assignment `a[i] = v` and `a[i][j] = v` mutate the collection in place
  and follow the same outer-variable mutability rules as `use mut`.

---

## Scope

Echo uses **lexical scoping**.

A name resolves to the innermost enclosing declaration at the **definition site**,
not the call site.

```echo
x: int = 10;

fn foo() {
    say(x);   // reads the global x
}
```

### Blocks

`if`, `else`, `while`, `for`, and `foreach` create block scopes.
Declarations inside a block do not leak out.
Assignments to an already-declared name update that binding.

### Functions

A function call creates a function scope whose parent is the
environment where the function was **defined** (its closure).

Parameters are locals of that function scope.

Nested functions capture that enclosing environment.

---

## Mutability

Variables are mutable in the scope that declared them.

`const name: T = expr;` declares an immutable binding. The type is required,
same as an ordinary declaration, and the initializer is required.

- Reassignment of that name (`x =`, `x +=`, and the other compound assigns)
  is a semantic error (**E3201**).
- Collection mutation through that name (`push`, `xs[i] = v`, hash field set,
  and other mutating methods) is a semantic error (**E3202**).
- The bound list or hash is frozen. Mutating that value through another name
  or a function parameter aborts (**E3203**). Reading, iterating, and helpers
  that return a new collection (`map`, `unique`, `clone`) are allowed.
- Nested collections reached through a *different* mutable name are not
  deep-frozen.
- `export const name: T = expr;` is allowed. Ordinary exports stay Model A:
  imported non-const collections keep shared mutable identity.
- `use mut name;` of a const binding is a semantic error (**E3204**).
- `watch` on a const name is legal and will not fire from that binding.
- Function parameters stay mutable. `const` on parameters is not in 0.7.0.

Destructuring unpacks a list or hash into names in one declaration or assignment.

- Declare: `[a: int, b: int] = pair;` and `{ id: int, name: str } = user;`. Types are required on fresh names.
- `const [lo: int, hi: int] = bounds;` makes each bound name const.
- Assignment to already-declared names omits types: `[a, b] = pair;` and `{ id, name } = user;`.
- Function parameters use the same patterns: `fn add([a: int, b: int]) -> int`. The parameter is a `list` or `hash`.
- List rest is last: `[head: int, rest: int...] = xs` binds `rest` as a `list` of that element type. No hash rest. No `as` rename.
- Length mismatch without rest aborts (**E3205**). Missing hash keys abort (**E2711**). Extra hash keys in patterns are ignored. Nested list patterns such as `[[a: int], b: int]` are allowed.

Inside a function:

- **Reads** of outer names are allowed (lexical).
- **Reassignment** of an outer name requires `use mut name;` in **that** function.
- Nested functions do not inherit `use mut` from the enclosing function.
- Collection mutation on an outer name (`push`, `arr[i] = v`, and other
  mutating methods) also requires `use mut name;`.

```echo
count: int = 0;

fn bump() {
    use mut count;
    if true {
        count = count + 1;   // legal: import applies to nested blocks
    }
}
```

`use name;` is allowed and documents a read-only import.
It does not permit reassignment.

`use` / `use mut` are only valid inside functions.
Importing an undefined name is an error.
Importing the same name twice in one function is an error.

Function arguments are local copies of references to mutable collections.
Rebinding a parameter does not rebind the caller’s variable.
Mutating a list/hash parameter mutates the shared collection.

---

## Functions

```echo
fn add(a: int, b: int) -> int {
    return a + b;
}

fn square(x: int) -> int => x * x;
```

- Every parameter needs a type.
- A `return` statement requires a return type annotation.
- `return;` yields `null`.
- `-> void` forbids a non-null return.
- Calls support positional and keyword arguments.
- Positional arguments cannot follow keyword arguments.
- Missing, extra, unexpected, and duplicate arguments are semantic errors.
- Default parameters: `punct: str = "!"`. Once a default appears, later
  non-variadic parameters must also have defaults.
- A trailing variadic: `parts: int...` binds extra positionals as a `list`
  of that type. Defaults come before the variadic. The variadic itself has
  no default expression; omitting it binds `[]`.
- Defaults are evaluated at call time, only when the argument is omitted.
  A default that aborts still aborts.
- No overloads.

Function values use the type `fn(int) -> int` (parameter types only, then
a required return type; no `?` or default markers). A function whose
trailing parameters have defaults is assignable to that full-arity type
and to a narrower type that omits those defaulted parameters:
`fn(x: int, y: int = 0) -> int` matches `fn(int, int) -> int` and
`fn(int) -> int`, not `fn() -> int`. Calls through the narrower type pass
only the provided arguments; defaults are filled at call time. Required
parameters and variadics still have to match the type (`...` is not
treated as optional). Lambdas are `fn(x: int) -> int { ... }` or the
inline `fn(x: int) -> int => x * 2`. Named functions are values: assign,
pass, return, and call through a function-typed or `dynamic` variable.

`order(comparator)` accepts a function value, a lambda, or a function name
string.

List `map(items, f)` / `filter(items, f)` (and `items.map(f)` / `items.filter(f)`)
apply a unary function value or lambda. `map` returns a new list of results.
`filter` keeps elements where `f` returns `true`; the callback must return
`bool` (not a truthy `int`). A callback that aborts aborts the whole call.
Empty list returns empty list. The input list is not mutated. `map` is list
only. `filter` also accepts a hash (below).

List `reduce(items, init, f)` (and `items.reduce(init, f)`) folds a binary
function value or lambda over the list. `init` is required. `f` takes
exactly two parameters `(accumulator, element)` and returns the next
accumulator. Empty list returns `init` and does not call `f`. Each callback
result must match `init`'s type. A callback that aborts aborts the whole
call. The input list is not mutated. List only. No `fold` twin.

List `forEach(items, f)` (and `items.forEach(f)`) calls a unary function
value or lambda on each element and discards the return value. The builtin
returns `null`. Empty list does not call `f` and returns `null`. A callback
that aborts aborts the whole call. The input list is not mutated. List only.

List `flatMap(items, f)` (and `items.flatMap(f)`) applies a unary function
value or lambda. Each callback result must be a `list`. Those lists are
concatenated **one** level into a new list. Nested lists inside a callback
result stay nested. Empty list returns empty list and does not call `f`.
A callback that aborts aborts the whole call. The input list is not mutated.
List only.

List `some(items, f)` / `every(items, f)` / `findIndex(items, f)` (and
`items.some(f)` / `items.every(f)` / `items.findIndex(f)`) apply a unary
function value or lambda that must return `bool` (same rule as `filter`:
not a truthy `int`). `some` is `true` if any element matches; empty list
is `false`. `every` is `true` if all match; empty list is `true`.
`findIndex` is the first matching index, or `-1` if none. `find(value)`
stays value search and is not overloaded. `some` and `findIndex` stop on
the first `true`; `every` stops on the first `false`. A callback that
aborts aborts the whole call. The input list is not mutated. List only.

List `zip(left, right)` (and `left.zip(right)`) pairs two lists into a new
list of 2-element lists `[left[i], right[i]]`. Length is the shorter of
the two; unequal lengths are not an error. Empty either side returns
empty list. The inputs are not mutated. List only.

List `unique(items)` (and `items.unique()`) returns a new list of first
occurrences in original order, using Echo `==` (`true` is not `1`). Empty
list returns empty list. The input is not mutated. List only.

List `chunk(items, size)` (and `items.chunk(size)`) returns a new list of
lists of length `size`; the last chunk may be shorter. `size` must be an
`int` `>= 1`. Empty list returns empty list. The input is not mutated.

List `flatten(items)` (and `items.flatten()`) concatenates **one** level
of nested lists into a new list. Empty list returns empty list. A
top-level element that is not a list is a type error. Nested lists inside
those elements stay nested. The input is not mutated. List only.

List `partition(items, f)` (and `items.partition(f)`) returns a two-element
list `[matches, rest]`. Unary `f` must return `bool` (same rule as
`filter`: not a truthy `int`). Empty list returns `[[], []]`. A callback
that aborts aborts the whole call. The input is not mutated. List only.

`rangeList(start, end)` returns the `list` of `int` values that
`for i in start...end` would visit (exclusive end, step `1`).
`rangeListInclusive(start, end)` matches `for i in start..end` (inclusive
end). Empty when that `for` would not iterate. This is a builtin, not
range-as-a-value syntax; `0...10` is not a list.

`mapValues(h, f)` (and `h.mapValues(f)`) returns a new hash with the same
keys. Unary `f` is called with each value. Empty hash returns empty hash.
Hashes preserve insertion order, and so does `mapValues`. The input is
not mutated.

`filter` on a hash (standalone `filter(h, f)` or `h.filter(f)`) keeps
entries where unary `f(value)` returns `true` (`bool` only — not a
truthy `int`). The first argument / receiver selects list vs hash.
Empty hash returns empty hash. Insertion order is preserved. The input
is not mutated. A callback that aborts aborts the whole call.

`return` outside a function is a semantic error.
Functions may recurse.

---

## Evaluation order

- Operands of `+ - * / %` and comparisons evaluate left, then right.
- `&&` and `||` short-circuit.
- Call arguments evaluate left to right.
- Keyword arguments are bound after positional arguments.

---

## Control flow

- `if cond { } else { }` and `else if`
- `while cond { }`
- `for i: int in start..end by step { }` — `..` inclusive, `...` exclusive
- start, end, and step are numeric expressions converted to `int`
- `bool`, `null`, and non-numeric values are not convertible loop bounds
- `by 0` is a runtime error
- `foreach item: T in iterable { }` — iterable must be a `list` or `hash`
- hashes iterate their keys as `str`
- `break` and `continue` are only valid inside loops (semantic error otherwise)

Conditions use truthiness.

---

## Collections

- List indexes are `int` in range `[0, length)`.
- Hash keys used in `[]` must be `str`.
- Out-of-range list/string indexes and missing hash keys are runtime errors.
- Slice syntax `xs[1:4]` (colon required) desugars to `slice(start, end)`
  with the same rules: start and end in `[0, length]`, end exclusive, no
  negatives, out of bounds aborts. Omitted start is `0`; omitted end is
  `length`. `xs[1:]`, `xs[:4]`, and `xs[:]` are allowed (`xs[:]` is a
  shallow list copy or the full string). `xs[]` is not a slice. There is
  no step form `xs[1::2]`.
- `clone()` is a shallow copy.

### `find`

`list.find(value)` returns the first index, or `-1` if missing.

### `removeValue`

`list.removeValue(value)` removes the first match.
It is an error if the value is not present.

### `reverse`

- On a string: returns a new reversed string.
- On a list: reverses the list **in place** and returns it.

### `format`

`"Hello, {}".format(name)` substitutes positional placeholders.
Standalone `format(template, ...)` uses the first argument as the template
and the remaining arguments as values.

---

## Number literals

Integers: `1`, `42`.

Floats: `2.5`, `.5`, `1e3`, `1e-3`, `1.5e+2`. Scientific forms are `float`.

A trailing dot is not a float: `5.` is the integer `5` followed by `.`, so
`5.asInt()` stays a method call.

`1..10` remains a range (`1` then `..` then `10`).

---

## Strings

Quotes: `"..."` and `'...'`.

Triple quotes: `"""..."""` and `'''...'''`. These may span lines.

Escapes: `\\`, `\"`, `\'`, `\n`, `\t`, `\r`.

Interpolation `${expression}` is allowed in both quote styles and in triples,
including at the start of the string (`"${name}"`).
Escapes in the literal fragments are processed.

Single-line `"..."` / `'...'` strings still reject a raw newline (lex error).
Triples may contain newlines.

Unterminated `/*` comments are a lex error.

---

## `watch`

```echo
watch counter;
```

Reports changes to the named binding from assignment and mutating operations,
including indexed assignment.

---

## Errors

Echo errors are Echo errors.

The implementation must not surface raw Python exceptions such as
`ValueError: invalid literal for int()` or `IndexError: list index out of range`.

Categories:

- lex
- parse
- semantic
- type
- name
- argument
- index
- mutation
- runtime

Diagnostics include file, line, and column when available.

Recovery is inquiry and `*Or` twins, not `try` / `catch`. Abort stays the
default. See `docs/failure-model.md`.

---

## Execution model

```text
Source → Lexer → Tokens → Parser → Typed AST → Semantic analyzer → Interpreter
```

There is no bytecode VM in v0.2.
One source file is one program. There is no module system in v0.2.

v0.3 adds a file-based module system on top of this pipeline. A program
that contains no `import` keeps the v0.2 execution model unchanged.
See `docs/module-semantics.md`.

v0.4 adds host and standard-library builtins (`args`, `env`, files, JSON,
`split` / `replace` / `contains` / `has` / `slice`) and corrects conversion
so `asInt(true)` / `asFloat(true)` are type errors. No new syntax.
v0.4.1 adds `join`, `startsWith`, `endsWith`, `fileExists`, and `echo check`.
v0.4.2 adds `cwd`, `exit`, `isDir`, and `listFiles`.
v0.4.3 adds `mkdir`, `removeFile`, string `indexOf` / `lastIndexOf` / `repeat` / `padStart` / `padEnd` / `replaceFirst`, numeric `abs` / `min` / `max` / `floor` / `ceil`, and `eprint`.
v0.5.0 adds `assert`, `copyFile`, `pathJoin`, `run`, `now`, `random` / `randomInt`, `readLine`, a REPL, `echo test`, triple-quoted multiline strings, and `.5` / scientific number literals.
v0.5.3 adds `readFileOr`, `parseJsonOr`, `asIntOr`, and `asFloatOr`.
v0.5.4 adds `echo fmt`.
v0.5.5 adds `fail(message)` and `echo lint`.
v0.5.6 adds the native `echo test` product: `expect` / `expectEq` / `expectNeq`, file and `fn testXxx()` units, and a pass/fail summary. No new keywords.
v0.5.7 adds VS Code / Cursor tasks and problem matchers for `echo check` / `fmt` / `lint` / `test`. No LSP. No new keywords.
v0.5.8 adds `echo lint` rules `test-naming`, `self-assign`, and `unreachable-after-fail`. No new keywords.
v0.5.9 makes `echo check [paths...]` recurse directories like `fmt` / `lint` / `test`, and adds **Echo: Check workspace**. No new keywords.
v0.6.0 adds first-class functions including lambdas (`fn(x: int) -> int { ... }`, type `fn(int) -> int`), slice syntax `xs[1:4]`, and user `fn` default plus variadic parameters.
v0.6.1 adds list `map` / `filter` on those function values.
v0.6.2 adds list `reduce` (`init` required; empty list returns `init`).
v0.6.3 adds list `forEach` (unary callback; return discarded; yields `null`).
v0.6.4 adds list `flatMap` (unary callback must return a list; concatenates one level).
v0.6.5 adds list `some` / `every` / `findIndex` (unary `bool` predicates; `find(value)` stays value search).
v0.6.6 allows omitting slice bounds: `xs[1:]`, `xs[:4]`, and `xs[:]` (omitted start is `0`, omitted end is `length`).
v0.6.7 adds list `zip` (pairs two lists to min length) and `unique` (first occurrences in order, Echo `==`).
v0.6.8 adds `echo test -run` (glob on `testXxx` function names), list `chunk`, `rangeList` / `rangeListInclusive` (same bounds as `...` / `..`), and hash `mapValues` / `filter`.
v0.6.9 adds function-type assignability for trailing defaults, list `flatten` / `partition`, and `echo test --json`. This is the last 0.6.x slice.
v0.7.0 adds `const` bindings (`const name: T = expr;`, optional `export const`). The bound list or hash is frozen. Function parameters stay mutable.
v0.7.1 adds destructuring (`[a: int, b: int] = pair;`, `{ id: int, name: str } = user;`, rest, assignment, fn params).
v0.7.2 adds `exact { ... }` object types. Extra exact fields are **E3208** and missing exact fields are **E3209**. No `as` rename, hash rest, unions, `switch`, builtins-as-values, or range-as-value.
See `docs/v0.4-stdlib.md`.
