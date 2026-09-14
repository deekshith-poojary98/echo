# Lists in Practice

Mutation, sort, and count.

```echo
items: list = [3, 1, 2, 3];
items.push(5);
items.order();
say(items);
say(items.countOf(3));
```

```text
[1, 2, 3, 3, 5]
2
```

## Notes

- `order()` sorts in place.
- `countOf()` counts exact value matches.
- `map(f)` / `filter(f)` return a new list from a function value or lambda.
- `reduce(init, f)` folds from required `init`; empty list returns `init`.
- `flatMap(f)` concatenates callback lists one level into a new list.
- `some(f)` / `every(f)` / `findIndex(f)` are bool predicates; `find(value)` is value search.
- `zip(other)` pairs to the shorter length. `unique()` keeps first occurrences in order.
- `flatten()` concatenates one level of nested lists. `partition(f)` splits into `[matches, rest]`.

## See Also

- [Lists](/core-concepts/lists)
- [Built-in Methods](/standard-library/built-in-methods)
