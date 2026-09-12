# Lists in Practice

## Overview
A practical list example using mutation, sorting, and counting.

## Syntax
```echo
items: list = [3, 1, 2, 3];
```

## Example
```echo
items: list = [3, 1, 2, 3];
items.push(5);
items.order();
say(items);
say(items.countOf(3));
```

## Output
```text
[1, 2, 3, 3, 5]
2
```

## Notes
- `order()` sorts the list in place.
- `countOf()` counts exact value matches.
- `map(f)` / `filter(f)` return a new list from a function value or lambda.
- `reduce(init, f)` folds from required `init`; empty list returns `init`.
- `flatMap(f)` concatenates callback lists one level into a new list.
- `some(f)` / `every(f)` / `findIndex(f)` are bool predicates; `find(value)` stays value search.

## See Also
- [Lists](/core-concepts/lists)
- [Built-in Methods](/standard-library/built-in-methods)
