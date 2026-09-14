# Scope, use, and watch

Lexical scoping. Functions can read outer variables from the scope where they were defined. Reassigning those outer variables still requires `use mut`.

## Syntax

```echo
use name;
use mut count;
watch count;
```

## Example

```echo
count: int = 0;
watch count;

fn bump() {
    use mut count;
    count = count + 1;
}

bump();
```

```text
WATCH: count changed to 1 (in bump)
```

## Notes

### `use`

Import an outer variable for reading inside a function.

### `use mut`

Import an outer variable for mutation inside a function.

### `watch`

Mark a variable for change reporting.

### Shadowing

A local typed variable with the same name as a parent variable can trigger a warning.

## Common Mistakes

- Reading outer variables without `use`
- Mutating outer variables without `use mut`
- Watching an undefined variable

## Current Limitation

Function scope is stricter than typical lexical closures. That is intentional.

## See Also

- [Functions](/getting-started/functions)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
