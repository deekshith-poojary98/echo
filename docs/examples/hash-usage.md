# Hash Usage

## Overview
A practical hash example using creation, update, and `ensure()`.

## Syntax
```echo
stats: hash = { hits: 1 };
```

## Example
```echo
stats: hash = { hits: 1 };
stats["hits"] = stats["hits"] + 1;
stats.ensure("misses", 0);
say(stats);
```

## Output
```text
{"hits": 2, "misses": 0}
```

## Notes
- Hash indexing uses string keys.
- `ensure()` is useful for defaults.

## See Also
- [Hashes](/core-concepts/hashes)
- [Type Aliases](/core-concepts/type-aliases)
