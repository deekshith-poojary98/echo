# Loops Reference

Compact reference for loop forms.

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

- Loop variable must be typed as `int`
- `..` is inclusive; `...` is exclusive
- Optional `by` sets the step
- Start, end, and step convert to `int` at runtime
- `by 0` aborts (**E2702**)
- Dedicated numeric `for` does **not** allocate a list

## Range as a value (0.7.4)

`start...end` and `start..end` (optional `by step`) are expressions that produce a `list` of `int`, matching `rangeList` / `rangeListInclusive` for step `1`.

```echo
xs: list = 0...5;          // [0, 1, 2, 3, 4]
ys: list = 0..5;           // [0, 1, 2, 3, 4, 5]
zs: list = 0...10 by 2;
```

`for i: int in 0...10` stays the non-allocating loop. `foreach i: int in 0...10` iterates the allocated list value. Slice syntax stays colon (`xs[1:4]`); `xs[0...10]` indexes with a list and is a type error.

## `foreach`

- Iterates a runtime iterable (`list`, or `hash` keys as `str`)
- Each element is checked against the declared binding type

## `break` and `continue`

Only valid inside loops.

## Common Mistakes

- `for i: str in 0..10 { ... }` — loop var must be `int`
- `break;` outside a loop
- `by 0` — aborts (**E2702**)

## See Also

- [Control Flow](/getting-started/control-flow)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
