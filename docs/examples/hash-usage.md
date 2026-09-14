# Hash Usage

Create, update, and `ensure()`.

```echo
stats: hash = { hits: 1 };
stats["hits"] = stats["hits"] + 1;
stats.ensure("misses", 0);
say(stats);
```

```text
{"hits": 2, "misses": 0}
```

## Notes

- Indexing uses string keys.
- `ensure()` returns the existing value or sets and returns the default.

## See Also

- [Hashes](/core-concepts/hashes)
- [Type Aliases](/core-concepts/type-aliases)
