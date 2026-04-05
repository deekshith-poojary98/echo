# Loops Reference

## Overview
A compact reference for Echo loop forms.

## Syntax
```echo
while condition { ... }
for i: int in 0..10 { ... }
for i: int in 0...10 by 2 { ... }
foreach item: str in items { ... }
```

## `while`
Runs while the condition stays truthy.

## `for`
- Variable must be typed as `int`
- `..` is inclusive
- `...` is exclusive
- `by` sets the step
- start, end, and step are converted to `int` at runtime

## `foreach`
- Iterates over the runtime iterable
- Each element is checked against the declared type

## `break` and `continue`
Only valid inside loops.

## Common Mistakes
- `for i: str in 0..10 { ... }`
- `break;` outside a loop
- `by 0`

## Current Limitation
`by 0` is not guarded and can produce a non-terminating loop.

## See Also
- [Control Flow](/getting-started/control-flow)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
