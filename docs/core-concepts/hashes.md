# Hashes

## Overview
Hashes are Echo's mutable key-value maps.

## Syntax
```echo
user: hash = { name: "Echo", active: true };
name: str = user["name"];
user["active"] = false;
```

## Example
```echo
user: hash = { name: "Ada", active: true };
user["role"] = "admin";
say(user);
say(user.keys());
```

## Output
```text
{"name": "Ada", "active": true, "role": "admin"}
["name", "active", "role"]
```

## Notes
- Hash literal keys can be identifiers or string literals.
- Bare identifier keys become string keys.
- Runtime indexing requires a string key.
- `ensure()` is useful for bucket-building and counters.
- `take()` and `take_last()` mutate the hash.
- `mapValues(f)` returns a new hash with the same keys. `filter(f)` keeps entries where `f(value)` is `true`.
- Hash iteration order is insertion order; `mapValues` / `filter` preserve it.
- A hash bound with `const` is frozen; field assignment and mutating methods abort.
- Destructuring unpacks listed keys: `{ id: int, name: str } = user;`. Missing keys abort. Extra keys are ignored.

## Common Mistakes
- Using non-string keys in runtime indexing
- Expecting missing keys to return `null`
- Forgetting that `take()` removes the key

## Current Limitation
- Hash indexing only accepts string keys.
- Key-value types are not generic.

## See Also
- [Built-in Methods](/standard-library/built-in-methods)
- [Type Aliases](/core-concepts/type-aliases)
- [Hash Usage](/examples/hash-usage)
