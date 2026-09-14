# Lists

## Overview
Lists are Echo's mutable ordered collection type.

## Syntax
```echo
nums: list = [1, 2, 3];
first: int = nums[0];
nums[1] = 10;
```

## Example
```echo
nums: list = [1, 2, 3];
nums.push(4);
nums.insertAt(1, 99);
nums.removeValue(2);
say(nums);
```

## Output
```text
[1, 99, 3, 4]
```

## Notes
- Lists are mutable unless bound with `const` (the list value is then frozen).
- Destructuring unpacks a list: `[a: int, b: int] = nums;` or `[head: int, rest: int...] = nums;`. Length mismatch without rest aborts.
- Indexing requires an `int`.
- Nested indexing and nested assignment are supported.
- Slice syntax `xs[1:4]`, `xs[1:]`, `xs[:4]`, and `xs[:]` matches `slice()`.
- `clone()` returns a shallow copy.
- `order()` sorts ascending by default.
- `order(cmpFn)` uses a comparator function that returns `int`.
- `map(f)` / `filter(f)` return a new list. `filter` requires a `bool` callback.
- `reduce(init, f)` folds the list from required `init`. Empty list returns `init`.
- `forEach(f)` calls unary `f` for each element and returns `null`. Empty list is a no-op.
- `flatMap(f)` applies unary `f` that returns a list and concatenates one level into a new list. Empty list returns `[]`.
- `some(f)` / `every(f)` / `findIndex(f)` take a `bool` callback. Empty `some` is `false`; empty `every` is `true`; empty `findIndex` is `-1`. `find(value)` stays value search.
- `zip(other)` pairs two lists into `[a, b]` pairs up to the shorter length.
- `unique()` returns first occurrences in order using Echo `==`.
- `chunk(size)` splits into new sublists of length `size` (last may be shorter).
- `flatten()` concatenates one level of nested lists.
- `partition(f)` returns `[matches, rest]` from a `bool` callback.
- `rangeList(start, end)` / `rangeListInclusive(start, end)` build a `list` of `int` matching `...` / `..` `for` ranges. As of 0.7.4, `0...5` / `0..5` (and `by`) are the language form of the same values.

## Common Mistakes
- Calling list methods on non-list values
- Using out-of-range indexes
- Assuming `clone()` is deep

## See Also
- [Built-in Methods](/standard-library/built-in-methods)
- [Operators](/reference/operators)
- [Lists in Practice](/examples/lists-in-practice)
