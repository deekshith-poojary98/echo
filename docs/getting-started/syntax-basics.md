# Syntax Basics

Statements end with `;`. Blocks use `{ }`. Method calls chain with `.`.

## Basic Example

```echo
name: str = "Echo";

if name == "Echo" {
    say(name.upperCase());
}
```

## Output

```text
ECHO
```

## How It Works

```echo
value: int = 10;
value = value + 1;

if value > 10 {
    say("big");
} else {
    say("small");
}
```

#### Output

```text
big
```

- Every normal statement ends with `;`.
- `if`, `while`, `for`, `foreach`, and block-form `fn` use braces and do not take a trailing semicolon.
- Whitespace is mostly ignored outside tokens.
- Newlines improve readability; they are not syntax.
- Method chaining works on values that expose methods.

### Interactive input (needs stdin)

`ask` reads a line from standard input. Run this interactively (or pipe a line in). As a non-interactive file with no stdin it aborts with **E2824** (`end of input`):

```echo
name: str = ask("Name: ").trim().upperCase();
say(name);
```

## Common Mistakes

### Python-style bare blocks

```echo
while true
    say("loop");
```

### Treating newlines as statement terminators

```echo
name: str = "Echo"
age: int = 1;
```

### Treating `.` as property access on non-class values

On ordinary values (numbers, strings, lists, hashes, …), `a.b` is not field access — with `(...)` it is a method call (`name.upperCase()`).

Class instances are different: field and property access work (`p.x`, getters/setters). See [Variables and Types](/getting-started/variables-and-types#classes-nominal) and [Classes and Interfaces](/examples/classes-and-interfaces).

## Related

- [Variables and Types](/getting-started/variables-and-types)
- [Operators](/reference/operators)
- [Control Flow](/getting-started/control-flow)
