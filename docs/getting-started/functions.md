# Functions

## Overview
Echo functions are named, typed, and strict about scope.

## Syntax
```echo
fn greet(name: str) {
    say("Hello, ${name}!");
}

fn add(a: int, b: int) -> int {
    return a + b;
}

fn addPair([a: int, b: int]) -> int {
    return a + b;
}

fn greetUser({ name: str }) -> str {
    return name;
}

fn square(x: int) -> int => x * x;
```

## Example
```echo
fn describe(name: str, age: int) {
    say(name, "is", age);
}

describe(age: 21, name: "Alice");
```

Lambdas and function types:

```echo
double: fn(int) -> int = fn(x: int) -> int { return x * 2; };
say(double(21));
say(map([1, 2, 3], double));
say(reduce([1, 2, 3], 0, fn(acc: int, x: int) -> int { return acc + x; }));
forEach([1, 2, 3], fn(x: int) { say(x); });
say(flatMap([1, 2], fn(x: int) -> list { return [x, x]; }));
say(some([1, 2, 3], fn(x: int) -> bool { return x == 2; }));
say(every([1, 2, 3], fn(x: int) -> bool { return x > 0; }));
say(findIndex([1, 2, 3], fn(x: int) -> bool { return x == 3; }));
say(zip([1, 2], [10, 20]));
say(unique([1, 2, 1, true, 1]));
say(chunk([1, 2, 3, 4, 5], 2));
say(flatten([[1, 2], [3]]));
say(partition([1, 2, 3, 4], fn(x: int) -> bool { return x % 2 == 0; }));
say(rangeList(0, 5));
say(rangeListInclusive(0, 5));
say(mapValues({ a: 1, b: 2 }, double));
```

Defaults and a trailing variadic:

```echo
fn join(punct: str = ",", parts: str...) {
    say(parts.join(punct));
}

join(parts: ["a", "b"]);
join(" | ", "a", "b", "c");
```

A function with trailing defaults is assignable to the full-arity type and to a narrower type that omits those defaulted parameters:

```echo
fn add(x: int, y: int = 0) -> int {
    return x + y;
}
full: fn(int, int) -> int = add;
narrow: fn(int) -> int = add;
say(full(2, 3));
say(narrow(2));
```

Standalone builtins are values too:

```echo
print: fn(str) -> dynamic = say;
print("hi");
apply: fn(list, fn(int) -> int) -> list = map;
say(type(say));
```

Variadic builtins (`say`, `eprint`, `format`, `pathJoin`) have type
`fn(dynamic...) -> void` or `fn(dynamic...) -> str`. Bound methods such as
`xs.map` are values; `xs.unknown` is still an error.

## Output
```text
Alice is 21
```

## Notes
### Parameter types
Every parameter needs a type annotation.

### Return types
Return type annotations are optional only when the function has no `return` statements.

If a function contains `return`, a return type annotation is required.

```echo
fn log(msg: str) {
    say(msg);
}

fn add(a: int, b: int) -> int {
    return a + b;
}
```

### `return;`
Bare `return;` is allowed.

### Keyword arguments
User-defined functions support keyword arguments.
Most builtins do too, except variadic ones (`say`, `format`).

### Scope inside functions
Functions can read outer variables lexically.
Reassignment of an outer variable still needs:

```echo
use x;
use mut x;
```

## Common Mistakes
### Reading an outer variable without `use`
```echo
name: str = "Echo";

fn greet() {
    say(name);
}
```

### Writing an outer variable without `use mut`
```echo
count: int = 0;

fn bump() {
    count = count + 1;
}
```

### Returning the wrong type from an annotated function
That raises a runtime type error.

## Current Limitation
- No overloads
- Range expressions are not values yet

## See Also
- [Scope, use, and watch](/core-concepts/scope-use-watch)
- [Built-in Methods](/standard-library/built-in-methods)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
