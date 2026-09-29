# Lesson 4 — Repeating things

**You are here**

1. Your first program ✓
2. Values and variables ✓
3. Making decisions ✓
4. **Repeating things** ←
5. Functions
6. Lists and hashes
7. Strings
8. Organizing programs
9. Classes

## What are we learning?

A **loop** repeats instructions while a condition stays true.

## Smallest useful loop: `while`

```echo
i: int = 1;

while i <= 3 {
    say(i);
    i = i + 1;
}
```

### Output

```text
1
2
3
```

### What happens

1. Start with `i` as `1`.
2. Ask: is `i` less than or equal to `3`? Yes → print `i`, then add `1` to `i`.
3. Repeat until the answer is no.

::: warning Do not forget to change the condition
If you never change `i`, the loop can run forever. Always move toward finishing the condition.
:::

## Counting with `for`

When you want a range of whole numbers, `for` is handy:

```echo
for n: int in 1..3 {
    say(n);
}
```

### Output

```text
1
2
3
```

`1..3` means from `1` through `3` (both ends included).

## Try it

Change the loop so it prints `1` through `5`.

## Predict it

```echo
i: int = 0;

while i < 2 {
    say("hi");
    i = i + 1;
}
```

<details>
<summary>Show answer</summary>

```text
hi
hi
```

</details>

## Fix it

This never ends (and will hang until stopped):

```echo
while true {
    say("loop");
}
```

Use a condition that becomes false, like `i <= 3`, and update `i` inside the loop.

## Deeper (later)

`break`, `continue`, `foreach`, and `...` (exclusive ranges) are in [Control Flow (full)](/getting-started/control-flow) and [Loops Reference](/reference/loops-reference).

## Next

→ [Lesson 5 — Functions](/learn/functions)
