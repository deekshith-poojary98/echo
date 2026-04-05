# Syntax Basics

## Overview
Echo uses a simple, C-style syntax: semicolons end statements, braces define blocks, and method calls can be chained.

## Syntax
```echo
name: str = "Echo";

if name == "Echo" {
    say(name.upperCase());
}
```

## Example
```echo
value: int = 10;
value = value + 1;

if value > 10 {
    say("big");
} else {
    say("small");
}
```

## Output
```text
big
```

## Notes
- Every normal statement ends with `;`.
- `if`, `while`, `for`, `foreach`, and block-form `fn` use braces and do not take a trailing semicolon.
- Whitespace is mostly ignored outside tokens.
- Newlines improve readability, but they are not syntax.
- Method chaining works on expressions:

```echo
name: str = ask("Name: ").trim().upperCase();
```

## Common Mistakes
### Adding Python-style bare blocks
```echo
while true
    say("loop");
```

### Treating newlines as statement terminators
```echo
name: str = "Echo"
age: int = 1;
```

### Forgetting that `.` starts method calls
`a.b` is not property access in the object-oriented sense. It is method-call syntax when followed by `(...)`.

## See Also
- [Variables and Types](/getting-started/variables-and-types)
- [Operators](/reference/operators)
- [Control Flow](/getting-started/control-flow)
