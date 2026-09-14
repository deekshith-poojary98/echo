# Syntax Basics

Statements end with `;`. Blocks use `{ }`. Method calls chain with `.`.

```echo
name: str = "Echo";

if name == "Echo" {
    say(name.upperCase());
}
```

```echo
value: int = 10;
value = value + 1;

if value > 10 {
    say("big");
} else {
    say("small");
}
```

```text
big
```

## Notes

- Every normal statement ends with `;`.
- `if`, `while`, `for`, `foreach`, and block-form `fn` use braces and do not take a trailing semicolon.
- Whitespace is mostly ignored outside tokens.
- Newlines improve readability; they are not syntax.
- Method chaining:

```echo
name: str = ask("Name: ").trim().upperCase();
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

### Treating `.` as field access

`a.b` is not OO property access. With `(...)` it is a method call.

## See Also

- [Variables and Types](/getting-started/variables-and-types)
- [Operators](/reference/operators)
- [Control Flow](/getting-started/control-flow)
