# Lesson 8 — Organizing programs (modules)

**You are here**

1–7 done · **8. Organizing programs** ← · 9 next

## What are we learning?

A **module** is one `.echo` file.

You can **export** names from one file and **import** them in another, so a program can live in more than one file.

## Why split a program?

- Keep related code together (math in one file, the starting file in another).
- Reuse the same function from more than one place.
- Make large programs easier to read.

## Two files in the same folder

Save both files in **the same folder**.

### `math.echo`

```echo
export fn add(a: int, b: int) -> int {
    return a + b;
}
```

`export` means: other files are allowed to import `add`.

### `app.echo`

```echo
import add from "math";

say(add(2, 3));
```

`import add from "math";` means: use `add` from the file `math.echo` next to this one.

## Which file do you run?

Run the file that **starts** the program — here, `app.echo`:

```bash
elang app.echo
```

Run this command from the **folder that contains both files**.

### Output

```text
5
```

You do **not** run `math.echo` by itself for this example. It provides `add`; `app.echo` uses it.

## Try it

Add `export fn double(n: int) -> int { return n * 2; }` to `math.echo`. Import it in `app.echo` and print `double(4)`.

## Predict it

If `app.echo` imports `add` and prints `add(10, 1)`, what prints?

<details>
<summary>Show answer</summary>

```text
11
```

</details>

## Fix it — forgot `export`

If `add` is not marked `export`, importing it fails. Add `export` in front of the function in `math.echo`.

## Deeper (later)

Relative paths, `std/…` imports, and full rules: [Modules (full)](/getting-started/modules) and [Module Semantics](/module-semantics).

::: tip Playground note
The browser playground runs **one** editor buffer. Multi-file modules need the installed `elang` CLI (or a clone with examples).
:::

## Next

→ [Lesson 9 — Classes](/learn/classes)
