# Lesson 2 — Values and variables

**You are here**

1. Your first program ✓
2. **Values and variables** ←
3. Making decisions
4. Repeating things
5. Functions
6. Lists and hashes
7. Strings
8. Organizing programs
9. Classes

## What are we learning?

A **value** is a piece of data: text, a number, true/false, and so on.

A **variable** is a **name** that refers to a value, so you can use that value again.

## The idea in ordinary language

Think of a labeled box:

- The **label** is the variable name (`name`).
- What is **inside** the box is the value (`"Echo"`).

## Smallest useful example

```echo
name: str = "Echo";
say(name);
```

### Output

```text
Echo
```

### Line by line

1. `name` — the label (variable name).
2. `: str` — this name holds **text**. In Echo, `str` means text (short for “string”).
3. `= "Echo"` — put the text `Echo` in that name.
4. `;` — end of the instruction.
5. `say(name);` — print whatever `name` currently refers to (not the word `name`, but the value).

::: tip Why `: str`?
Echo requires a **type** on a new variable. A type is a short label for the kind of value allowed. You will see `str` (text), `int` (whole numbers), `bool` (`true` / `false`), and others later.
:::

## More kinds of values

```echo
title: str = "Echo";
users: int = 42;
ready: bool = true;

say(title, users, ready);
```

### Output

```text
Echo 42 true
```

- `int` — whole numbers (`1`, `42`, `-3`)
- `bool` — `true` or `false`

## Changing a value

After you declare a name, you can give it a new value of the **same** kind:

```echo
count: int = 1;
count = 2;
say(count);
```

### Output

```text
2
```

Notice the second line has **no** `: int` — the name already exists.

## Try it — change the value

Start from:

```echo
name: str = "Echo";
say(name);
```

Change `"Echo"` to your name and run again.

## Predict it

What will this print?

```echo
city: str = "Paris";
say(city);
```

<details>
<summary>Show answer</summary>

```text
Paris
```

</details>

## Fix it — name used before it exists

This fails:

```echo
count = 1;
```

Echo needs the type the first time:

```echo
count: int = 1;
```

## Deeper (later)

Unions, destructuring, `const`, `dynamic`, and class types are covered in [Variables and Types (full)](/getting-started/variables-and-types). Skip that until you finish the Learn path.

## Next

→ [Lesson 3 — Making decisions](/learn/making-decisions)
