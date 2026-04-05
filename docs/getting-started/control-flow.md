# Control Flow

## Overview
Echo supports the usual control flow for scripting: branching, loops, and loop control statements.

## Syntax
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

## Example
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

## Notes
### `if`, `else`, and `else if`
Echo supports the familiar `else if` source form.

### `while`
Runs while the condition stays truthy.

### `for`
- `..` means inclusive end
- `...` means exclusive end
- `by` sets the step
- loop variable type must be `int`

### `foreach`
Each item is checked against the declared loop variable type at runtime.

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

## Current Limitation
- `for ... by 0` is not guarded and can loop forever.

## See Also
- [Loops Reference](/reference/loops-reference)
- [Operators](/reference/operators)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
