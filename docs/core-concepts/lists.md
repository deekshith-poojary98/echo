# Lists

Mutable ordered collections. Type is `list`.

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

```text
[1, 99, 3, 4]
```

## Notes

- Mutable unless bound with `const` (then the list value is frozen).
- Destructuring: `[a: int, b: int] = nums;` or `[head: int, rest: int...] = nums;`. Length mismatch without rest aborts.
- Indexing requires an `int`. Nested index and nested assignment work.
- Slice syntax `xs[1:4]`, `xs[1:]`, `xs[:4]`, `xs[:]` matches `slice()`.
- `clone()` is a shallow copy.
- `order()` sorts ascending in place. `order(cmpFn)` uses a comparator that returns `int`.
- `map(f)` / `filter(f)` return a new list. `filter` requires a `bool` callback.
- `reduce(init, f)` folds from required `init`. Empty list returns `init`.
- `forEach(f)` calls unary `f` per element; returns `null`. Empty list is a no-op.
- `flatMap(f)` applies unary `f` that returns a list and concatenates one level. Empty → `[]`.
- `some(f)` / `every(f)` / `findIndex(f)` take a `bool` callback. Empty: `false` / `true` / `-1`. `find(value)` is value search.
- `zip(other)` pairs up to the shorter length.
- `unique()` keeps first occurrences in order (`==`).
- `chunk(size)` splits into sublists of length `size` (last may be shorter).
- `flatten()` concatenates one level of nested lists.
- `partition(f)` returns `[matches, rest]` from a `bool` callback.
- `rangeList(start, end)` / `rangeListInclusive(start, end)` match `...` / `..` `for` ranges. As of 0.7.4, `0...5` / `0..5` (and `by`) are the language form of the same values.

## Common Mistakes

- List methods on a non-list
- Out-of-range indexes
- Assuming `clone()` is deep

## See Also

- [Built-in Methods](/standard-library/built-in-methods)
- [Operators](/reference/operators)
- [Lists in Practice](/examples/lists-in-practice)
