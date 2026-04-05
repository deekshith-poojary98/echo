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
- Lists are mutable.
- Indexing requires an `int`.
- Nested indexing and nested assignment are supported.
- `clone()` returns a shallow copy.
- `order()` sorts ascending by default.
- `order(cmpFn)` uses a comparator function that returns `int`.

## Common Mistakes
- Calling list methods on non-list values
- Using out-of-range indexes
- Assuming `clone()` is deep

## See Also
- [Built-in Methods](/standard-library/built-in-methods)
- [Operators](/reference/operators)
- [Lists in Practice](/examples/lists-in-practice)
