# Modules

::: tip Learning Echo from scratch?
Start with [Lesson 8 — Organizing programs](/learn/modules). This page is the fuller module write-up.
:::

Split a program across `.echo` files with `export` and `import`. Each file is its own module scope. Full contract: [Module Semantics](/module-semantics).

## Basic Example

Two files in the same directory:

```echo
# math.echo

export fn add(a: int, b: int) -> int {
    return a + b;
}
```

```echo
# app.echo

import add from "math";

say(add(2, 3));
```

Run the entry file (from the directory that contains both files):

```bash
elang app.echo
```

## Output

```text
5
```

## How It Works

- Specifiers resolve relative to the importing file: `"math"`, `"./math"`, `"lib/math"`, `"../shared"`.
- Reserved `std/…` imports load from the Echo install tree (available after pip/pipx install):

```echo
import stdOk from "std/meta";

say(stdOk());
```

#### Output

```text
true
```

- Only `export`ed names are visible to importers. Private names stay in the defining module.
- `import` is not the same as `use` / `use mut` (those are function-scope capture / mutation).
- Nested demo in the repo: from a clone at the repo root, `elang examples/modules_demo/app.echo` prints:

```text
2+3 = 5
6^2 = 36
std ready: true
```

## Common Mistakes

- Expecting `math.add(...)` dotted namespaces — not supported; bind names with `import`.
- Pointing `elang examples/...` at a pipx-only install — `examples/` is clone-only.
- Forgetting `export` on the name you import.

## Related

- [Module Semantics](/module-semantics) — full path / cycle / std rules
- [Mini Programs](/examples/mini-programs)
- [Std Inventory](/reference/std-inventory)
- [CLI and Execution Model](/reference/cli-and-execution-model)
