# Control Flow

`if` / `switch` / `while` / `for` / `foreach`, plus `break` and `continue`. Conditions use Echo [truthiness](#truthiness). `switch` is value dispatch (literals, type arms, destructuring) — not error handling.

## Truthiness

Used by `if`, `while`, `&&`, `||`, `!`, and `default()`.

**Falsy** values: `false`, `null`, `0`, `0.0`, `""`, `[]`, `{}`.

Every other value is **truthy**.

Full contract: [Language Semantics — Truthiness](/language-semantics#truthiness).

## Basic Example

```echo
for i: int in 0..5 {
    if i == 2 {
        continue;
    }

    if i == 4 {
        break;
    }

    say(i);
}
```

## Output

```text
0
1
3
```

## How It Works

```echo
x: int = 1;
condition: bool = true;
items: list = ["a", "b"];

if condition {
    say("yes");
} else {
    say("no");
}

switch x {
    0 { say("zero"); }
    1 { say("one"); }
    else { say("other"); }
}

i: int = 0;
while i < 1 {
    say("loop");
    i = i + 1;
}

for n: int in 0..2 by 1 {
    say(n);
}

foreach item: str in items {
    say(item);
}
```

#### Output

```text
yes
one
loop
0
1
2
a
b
```

### `if`, `else`, and `else if`

`else if` is supported in source form.

### `while`

Runs while the condition stays truthy.

### `for`

- `..` means inclusive end
- `...` means exclusive end
- `by` sets the step
- `by 0` aborts (**E2702**)
- loop variable type must be `int`
- The same `..` / `...` / `by` spelling is a `list` of `int` in expression position (`xs: list = 0...5;`)

### `foreach`

Each item is checked against the declared loop variable type at runtime. A range expression is a list, so `foreach` over `0...3` iterates that list.

## Common Mistakes

### Using the wrong loop variable type in `for` — E1008

```echo
for i: str in 0..10 {
    say(i);
}
```

### Using `break` outside a loop — E1004

```echo
break;
```

That is a **semantic** error (**E1004**), not a syntax error.

### Forgetting braces

Echo does not support implicit blocks.

### `for ... by 0` — E2702

Aborts (**E2702**). It does not loop forever.

## Related

- [Loops Reference](/reference/loops-reference)
- [Operators](/reference/operators)
- [Language Semantics](/language-semantics)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
