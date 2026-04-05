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

fn square(x: int) -> int => x * x;
```

## Example
```echo
fn describe(name: str, age: int) {
    say(name, "is", age);
}

describe(age: 21, name: "Alice");
```

## Output
```text
Alice is 21
```

## Notes
### Parameter types
Every parameter needs a type annotation.

### Return types
Return type annotations are optional.

```echo
fn log(msg: str) {
    say(msg);
}
```

### `return;`
Bare `return;` is allowed.

### Keyword arguments
User-defined functions support keyword arguments.
Built-ins do not.

### Scope inside functions
Outer variables are not automatically visible inside functions.
Use:

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
- No default parameters
- No variadic functions
- No overloads
- No anonymous function values

## See Also
- [Scope, use, and watch](/core-concepts/scope-use-watch)
- [Built-in Methods](/standard-library/built-in-methods)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
