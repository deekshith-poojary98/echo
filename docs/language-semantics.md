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
```

Aliases are names for existing types. They are not new runtime types.
Object aliases require the listed fields and field types.
Extra fields are allowed.

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
- No default arguments, variadics, or overloads.

`return` outside a function is a semantic error.
Functions may recurse.
Functions are not first-class values in source syntax yet, except that
`order(comparator)` may refer to a function by name.

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

## Strings

Quotes: `"..."` and `'...'`.

Escapes: `\\`, `\"`, `\'`, `\n`, `\t`, `\r`.

Interpolation `${expression}` is allowed in both quote styles,
including at the start of the string (`"${name}"`).
Escapes in the literal fragments are processed.

Strings are single-line. A newline inside quotes is a lex error.

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
See `docs/v0.4-stdlib.md`.
