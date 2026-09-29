# Scope, use, and watch

Lexical scoping. Functions can **read** outer variables from the scope where they were defined. **Reassigning** those outer variables requires `use mut`. Plain `use name;` does **not** permit assignment.

## Syntax

```echo
use name;
use mut count;
watch count;
```

## Basic Example

```echo
count: int = 0;
watch count;

fn bump() {
    use mut count;
    count = count + 1;
}

bump();
```

## Output

```text
WATCH: count changed to 1 (in bump) at <file>:<line>:<col>
```

The stable prefix is `WATCH: count changed to 1 (in bump)`. A source location suffix `at file:line:col` is appended; the path and numbers depend on where you saved the file.

## How It Works

### Lexical reads

Outer names are visible for reading without `use`:

```echo
name: str = "Echo";

fn greet() {
    say(name);
}

greet();
```

#### Output

```text
Echo
```

### `use`

Optional explicit import of an outer name. It does **not** grant write access.

### `use mut`

Required before assigning to an outer variable inside a function.

### `watch`

Mark a variable for change reporting. Mutation lines include a source
location (`at file:line:col`). On abort, CLI / `elang test` also dump watched bindings under
`Watched:` and active call frames under `Stack:` (when the failure is
inside a call). Use `trace(value)` to print a value without changing it.

### Shadowing

A local typed variable with the same name as a parent variable can trigger a warning.

## Common Mistakes

### Mutating an outer variable without `use mut` — E2003

```echo
count: int = 0;

fn bump() {
    count = count + 1;
}

bump();
```

### Expecting plain `use` to allow assignment — E2003

```echo
count: int = 0;

fn bump() {
    use count;
    count = count + 1;
}
```

### Watching an undefined variable

`watch` requires a name that already exists in scope.

## Current Limitation

Reassignment of outer variables always needs `use mut`. That is intentional — see [Known Limitations](/errors-diagnostics/known-limitations).

## Related

- [Functions](/getting-started/functions)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
