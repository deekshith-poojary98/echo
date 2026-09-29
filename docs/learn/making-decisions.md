# Lesson 3 — Making decisions

**You are here**

1. Your first program ✓
2. Values and variables ✓
3. **Making decisions** ←
4. Repeating things
5. Functions
6. Lists and hashes
7. Strings
8. Organizing programs
9. Classes

## What are we learning?

Programs often need to **choose**: do this, or do that.

In Echo, `if` means: **if this is true, run the instructions inside `{ }`.**

## Smallest useful example

```echo
age: int = 18;

if age >= 18 {
    say("Adult");
}
```

### Output

```text
Adult
```

### Line by line

1. `age` holds the number `18`.
2. `age >= 18` asks: “Is age greater than or equal to 18?”
3. That question is **true**, so Echo runs what is inside `{ }`.
4. `say("Adult");` prints `Adult`.

If you change `age` to `15`, the condition is false, and Echo skips the block — nothing is printed.

## Adding an other choice: `else`

```echo
age: int = 15;

if age >= 18 {
    say("Adult");
} else {
    say("Under 18");
}
```

### Output

```text
Under 18
```

- If the condition is true → run the first block.
- Otherwise → run the `else` block.

## Try it

Change `age` to `21` and to `10`. Predict the output before you run.

## Predict it

```echo
score: int = 50;

if score >= 60 {
    say("Pass");
} else {
    say("Retry");
}
```

<details>
<summary>Show answer</summary>

```text
Retry
```

</details>

## Fix it — missing braces

Echo needs `{ }` around the instructions after `if`. This style is **not** allowed:

```echo
if true
    say("yes");
```

Use:

```echo
if true {
    say("yes");
}
```

## Deeper (later)

`else if`, `switch`, and the full list of “false-like” values are in [Control Flow (full)](/getting-started/control-flow).

## Next

→ [Lesson 4 — Repeating things](/learn/repeating-things)
