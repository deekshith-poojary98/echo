# Functions

Named `fn`s with typed parameters. Outer variables can be **read** lexically. **Reassignment** of an outer variable needs `use mut`. A `return` requires a return type on the function.

## Basic Example

```echo
fn greet(name: str) {
    say("Hello, ${name}!");
}

fn add(a: int, b: int) -> int {
    return a + b;
}

greet("Echo");
say(add(2, 3));
```

## Output

```text
Hello, Echo!
5
```

## How It Works

- Every parameter needs a type annotation.
- Return type annotations are optional only when the function has no `return` statements.
- If a function contains `return` (including bare `return;`), a return type annotation is required — use `-> void` when there is no value.
- Keyword arguments work on user-defined functions. Most builtins accept them too, except variadic ones (`say`, `format`, …).
- Functions can read outer variables without `use`. Only `use mut name;` permits assignment to an outer name.

### Keyword arguments

```echo
fn describe(name: str, age: int) {
    say(name, "is", age);
}

describe(age: 21, name: "Alice");
```

#### Output

```text
Alice is 21
```

### Other shapes

```echo
fn addPair([a: int, b: int]) -> int {
    return a + b;
}

fn greetUser({ name: str }) -> str {
    return name;
}

fn square(x: int) -> int => x * x;

say(addPair([2, 3]));
say(greetUser({ name: "Ada" }));
say(square(4));
```

#### Output

```text
5
Ada
16
```

### Lambdas and collection helpers

```echo
double: fn(int) -> int = fn(x: int) -> int { return x * 2; };
say(double(21));
say(map([1, 2, 3], double));
say(reduce([1, 2, 3], 0, fn(acc: int, x: int) -> int { return acc + x; }));
```

#### Output

```text
42
[2, 4, 6]
6
```

### Defaults and trailing variadic

```echo
fn join(punct: str = ",", parts: str...) {
    say(parts.join(punct));
}

join(parts: ["a", "b"]);
join(" | ", "a", "b", "c");
```

#### Output

```text
a,b
a | b | c
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

#### Output

```text
5
2
```

### Builtins as values

```echo
print: fn(str) -> dynamic = say;
print("hi");
say(type(say));
```

#### Output

```text
hi
fn
```

Variadic builtins (`say`, `eprint`, `format`, `pathJoin`) have type
`fn(dynamic...) -> void` or `fn(dynamic...) -> str`. Bound methods such as
`xs.map` are values; `xs.unknown` is still an error.

## Common Mistakes

### `return` without a return type — E1009

```echo
fn f() { return; }
```

Fails with **E1009**. Use an explicit return type:

```echo
fn f() -> void { return; }
```

### Assigning an outer variable without `use mut` — E2003

```echo
count: int = 0;

fn bump() {
    count = count + 1;
}

bump();
```

Reading `count` would work; assigning it needs `use mut count;` inside the function.

### `use` alone does not allow assignment

```echo
count: int = 0;

fn bump() {
    use count;
    count = count + 1;
}
```

Still **E2003**. Only `use mut count;` permits the assignment.

### Keyword args on variadic builtins — E2601

```echo
say(msg: "hi");
```

Fails with **E2601** (`say` is variadic and does not take keyword arguments).

## Current Limitation

- No overloads

## Related

- [Scope, use, and watch](/core-concepts/scope-use-watch)
- [Built-in Methods](/standard-library/built-in-methods)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
