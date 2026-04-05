# Language Reference

## Overview
This is the compact lookup page for Echo syntax and built-ins.

## Statements
```echo
name: str = "Echo";
name = "Echo 2";
if cond { ... }
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
- `int`
- `float`
- `str`
- `bool`
- `dynamic`
- `list`
- `hash`
- `void` for function return annotations only

## Literals
- Integers: `123`
- Floats: `12.34`
- Strings: `"hello"`, `'hello'`
- Booleans: `true`, `false`
- Null: `null`
- Lists: `[1, 2, 3]`
- Hashes: `{ key: value }`

## Operators
- Arithmetic: `+ - * / %`
- Comparison: `== != < > <= >=`
- Logical: `&& || !`
- Assignment: `=`

## Function Forms
```echo
fn name(a: int) { ... }
fn name(a: int) -> int { ... }
fn square(x: int) => x * x;
fn square(x: int) -> int => x * x;
```

If a function contains `return`, it must declare a return type.

## Notes
Use this page for quick lookup. For explanations and examples, go back to the guide pages.

## See Also
- [Built-in Methods](/standard-library/built-in-methods)
- [Operators](/reference/operators)
- [Variables and Types](/getting-started/variables-and-types)
