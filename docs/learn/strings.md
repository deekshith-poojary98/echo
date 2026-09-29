# Lesson 7 — Strings

**You are here**

1–6 done · **7. Strings** ← · 8–9 next

## What are we learning?

A **string** is text. In Echo its type name is `str`.

You already used strings with `say("Hello, Echo!");`. This lesson shows how to build text from variables.

## Putting a value inside text

```echo
name: str = "Echo";
say("Hello, ${name}!");
```

### Output

```text
Hello, Echo!
```

`${name}` means: insert the value of `name` here.

This only works inside quotes that Echo treats as interpolating strings (normal `"..."` and `'...'` strings do).

## Quotes

Both styles work for ordinary text:

```echo
a: str = "Echo";
b: str = 'Echo';
say(a, b);
```

### Output

```text
Echo Echo
```

## Try it

Store your name in a variable. Print `Hello, <your name>!` using `${...}`.

## Predict it

```echo
city: str = "Oslo";
say("City: ${city}");
```

<details>
<summary>Show answer</summary>

```text
City: Oslo
```

</details>

## Fix it — unfinished `${...}`

This fails (missing `}`):

```echo
say("Hello ${name");
```

Close the `${` with `}`.

## Deeper (later)

`format`, escapes, and triple-quoted blocks are in [Strings and Interpolation (full)](/getting-started/strings-and-interpolation).

## Next

→ [Lesson 8 — Organizing programs](/learn/modules)
