# Scope, use, and watch

## Overview
Echo uses lexical scoping. Functions can read outer variables from the scope where they were defined.
Reassigning those outer variables still requires `use mut`.

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

## Output
```text
WATCH: count changed to 1 (in bump)
```

## Notes
### `use`
Imports an outer variable for reading inside a function.

### `use mut`
Imports an outer variable for mutation inside a function.

### `watch`
Marks a variable for change reporting.

### Shadowing
Declaring a local typed variable with the same name as a parent variable can trigger a warning.

## Common Mistakes
- Reading outer variables without `use`
- Mutating outer variables without `use mut`
- Watching an undefined variable

## Current Limitation
Echo's function scope is stricter than typical lexical closures. That is intentional in the current implementation.

## See Also
- [Functions](/getting-started/functions)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
