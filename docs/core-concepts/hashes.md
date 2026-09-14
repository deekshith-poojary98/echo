# Hashes

Mutable key-value maps. Type is `hash`.

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

```text
{"name": "Ada", "active": true, "role": "admin"}
["name", "active", "role"]
```

## Notes

- Literal keys: identifiers or string literals. Bare identifiers become string keys.
- Runtime indexing requires a string key.
- `ensure()` sets a default if missing; returns the current value either way. Common for counters and buckets.
- `take()` and `take_last()` mutate the hash.
- `mapValues(f)` returns a new hash with the same keys. `filter(f)` keeps entries where `f(value)` is `true`.
- Iteration order is insertion order; `mapValues` / `filter` preserve it.
- A hash bound with `const` is frozen; field assignment and mutating methods abort.
- Destructuring: `{ id: int, name: str } = user;`. Missing keys abort. Extra keys are ignored (unless the type is `exact`).

## Common Mistakes

- Non-string keys at runtime
- Expecting a missing key to return `null` (it aborts)
- Forgetting that `take()` removes the key

## Current Limitation

- Runtime indexing: string keys only.
- Key and value types are not generic.

## See Also

- [Built-in Methods](/standard-library/built-in-methods)
- [Type Aliases](/core-concepts/type-aliases)
- [Hash Usage](/examples/hash-usage)
