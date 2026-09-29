# Lesson 5 — Functions

**You are here**

1. Your first program ✓
2. Values and variables ✓
3. Making decisions ✓
4. Repeating things ✓
5. **Functions** ←
6. Lists and hashes
7. Strings
8. Organizing programs
9. Classes

## What are we learning?

A **function** is a **named group of instructions** you can run whenever you need them.

## Smallest useful example

```echo
fn greet() {
    say("Hello!");
}

greet();
```

### Output

```text
Hello!
```

### Line by line

1. `fn greet()` — define a function named `greet` with no inputs.
2. `{ ... }` — the instructions that belong to `greet`.
3. `greet();` — **run** those instructions.

Defining a function does not run it. Calling `greet();` does.

## Inputs (parameters)

A **parameter** is a name for a value you pass in when you call the function.

```echo
fn greet(name: str) {
    say("Hello,", name);
}

greet("Echo");
```

### Output

```text
Hello, Echo
```

- `name: str` — this function expects text.
- `greet("Echo");` — pass the text `Echo` in.

## Answers back (`return`)

Some functions give a value back. You mark the kind of answer with `->`, and use `return`:

```echo
fn add(a: int, b: int) -> int {
    return a + b;
}

say(add(2, 3));
```

### Output

```text
5
```

- `-> int` — this function’s answer is a whole number.
- `return a + b;` — send that answer back to the caller.
- `say(add(2, 3));` — run `add`, then print the answer.

## Try it

Write a function `shout` that takes a `str` and prints it. Call it once.

## Predict it

```echo
fn twice(n: int) -> int {
    return n * 2;
}

say(twice(4));
```

<details>
<summary>Show answer</summary>

```text
8
```

</details>

## Fix it — `return` needs a return type

This fails:

```echo
fn f() {
    return;
}
```

If you use `return`, write a return type. For “no value,” use `void`:

```echo
fn f() -> void {
    return;
}
```

## Deeper (later)

Reading and changing names from outside a function (`use` / `use mut`), lambdas, and advanced shapes are in [Functions (full)](/getting-started/functions) and [Scope, use, and watch](/core-concepts/scope-use-watch). You do not need them yet.

## Next

→ [Lesson 6 — Lists and hashes](/learn/lists-and-hashes)
