# Functions in Practice

## Overview
A small example showing function calls, return values, and keyword arguments.

## Syntax
```echo
fn add(a: int, b: int) -> int {
    return a + b;
}
```

## Example
```echo
fn add(a: int, b: int) -> int {
    return a + b;
}

fn describe(name: str, score: int) {
    say(name, "scored", score);
}

result: int = add(3, 4);
describe(score: result, name: "Echo");
```

## Output
```text
Echo scored 7
```

## Notes
- Keyword arguments work for user-defined functions.
- Return types are checked when annotated.

## See Also
- [Functions](/getting-started/functions)
- [Scope, use, and watch](/core-concepts/scope-use-watch)
