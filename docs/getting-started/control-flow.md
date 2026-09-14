# Control Flow

`if` / `while` / `for` / `foreach`, plus `break` and `continue`. Conditions use Echo truthiness.

```echo
if condition {
    say("yes");
} else {
    say("no");
}

while condition {
    say("loop");
}

for i: int in 0..10 by 1 {
    say(i);
}

foreach item: str in items {
    say(item);
}
```

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

```text
0
1
3
```

## Notes
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
### Using the wrong loop variable type in `for`
```echo
for i: str in 0..10 {
    say(i);
}
```

### Using `break` outside a loop
That raises a syntax error.

### Forgetting braces
Echo does not support implicit blocks.

### `for ... by 0`
Aborts (**E2702**). It does not loop forever.

## See Also
- [Loops Reference](/reference/loops-reference)
- [Operators](/reference/operators)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
