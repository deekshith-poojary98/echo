# Lesson 6 — Lists and hashes

**You are here**

1–5 done · **6. Lists and hashes** ← · 7–9 next

## What are we learning?

A **list** is an ordered row of values: first, second, third, …

A **hash** is a collection of **labeled** values: each item has a name (a key) and a value.

## Lists

```echo
nums: list = [1, 2, 3];
say(nums[0]);
nums.push(4);
say(nums);
```

### Output

```text
1
[1, 2, 3, 4]
```

### What this does

| Line | Meaning |
| --- | --- |
| `nums: list = [1, 2, 3];` | Create a list with three numbers |
| `nums[0]` | The first item (counting starts at **0**) |
| `nums.push(4);` | Add `4` at the end |
| `say(nums);` | Print the whole list |

## Hashes

```echo
user: hash = { name: "Ada", active: true };
say(user["name"]);
user["role"] = "admin";
say(user);
```

### Output

```text
Ada
{"name": "Ada", "active": true, "role": "admin"}
```

- `{ name: "Ada", active: true }` — labels `name` and `active`.
- `user["name"]` — read the value for label `name`.
- `user["role"] = "admin";` — add or change a label.

## Try it

Make a list of three favorite foods (as text). Print the first one, then push a fourth food and print the list.

## Predict it

```echo
xs: list = ["a", "b"];
say(xs[1]);
```

<details>
<summary>Show answer</summary>

```text
b
```

</details>

## Fix it — wrong index

Lists start at `0`. For `[10, 20, 30]`, the last item is index `2`, not `3`. Asking for a missing index stops the program with an error.

## Deeper (later)

Full method lists (`map`, `filter`, `ensure`, …) live in [Lists (methods)](/core-concepts/lists) and [Hashes (methods)](/core-concepts/hashes).

## Next

→ [Lesson 7 — Strings](/learn/strings)
