# Language Reference

Compact lookup for syntax and built-ins. For explanations, use Getting Started.

## Statements

```echo
name: str = "Echo";
const count: int = 0;
name = "Echo 2";
[a: int, b: int] = pair;
{ id: int, name: str } = user;
{ id as userId: int } = user;
if cond { ... }
switch x { 0 { ... } else { ... } }
while cond { ... }
for i: int in 0..10 { ... }
foreach item: str in items { ... }
fn greet(name: str) { ... }
return;
break;
continue;
use name;
use mut count;
watch count;
```

## Built-in Types

- `int`, `float`, `str`, `bool`, `dynamic`, `list`, `hash`
- `void` — function return annotations only
- Unions: `int | str` (no `null` type member; prefer `str | void`)
- Object shapes: `{ id: int }` (open) and `exact { id: int }` (closed)
- Function types: `fn(int) -> int`

## Literals

- Integers: `123`; floats: `12.34`, `.5`, scientific form
- Strings: `"hello"`, `'hello'`, multiline `"""` / `'''`
- Booleans: `true`, `false`; null: `null`
- Lists: `[1, 2, 3]`; hashes: `{ key: value }`
- Ranges as values: `0...10`, `0..10`, optional `by`

## Operators

- Arithmetic: `+ - * / %`
- Comparison: `== != < > <= >=`
- Logical: `&& || !`
- Assignment: `=` and `+= -= *= /= %=`

## Function Forms

```echo
fn name(a: int) { ... }
fn name(a: int) -> int { ... }
fn square(x: int) => x * x;
fn square(x: int) -> int => x * x;
fn add(a: int, b: int = 0) -> int { return a + b; }
fn sum(parts: int...) -> int { ... }
```

Named functions and lambdas are values. Standalone builtins (`say`, `map`, …) and bound methods (`xs.map`) are values too (0.7.3). If a function contains `return`, it must declare a return type.

## Notes

Quick lookup only. Semantics contract: [language-semantics.md](/language-semantics). Guides live under Getting Started and Examples.

## See Also

- [Built-in Methods](/standard-library/built-in-methods)
- [Operators](/reference/operators)
- [Variables and Types](/getting-started/variables-and-types)
