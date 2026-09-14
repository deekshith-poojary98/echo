# Functions in Practice

Calls, returns, and keyword arguments.

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

```text
Echo scored 7
```

## Notes

- Keyword arguments work for user-defined functions.
- Annotated return types are checked.

## See Also

- [Functions](/getting-started/functions)
- [Scope, use, and watch](/core-concepts/scope-use-watch)
