# Type Aliases

Named aliases for builtins and object-shaped hash types.

## Syntax

```echo
type Age = int;
type User = { id: int, name: str, active: bool };
type ExactUser = exact { id: int, name: str, active: bool };
```

## Example

```echo
type User = { id: int, name: str, active: bool };

user: User = {
    id: 1,
    name: "Echo",
    active: true
};

say(user);
```

```text
{"id": 1, "name": "Echo", "active": true}
```

## Notes

- Use aliases in declarations and function parameters.
- Open object aliases check required fields and types; extra fields are allowed.
- `exact { ... }` requires exactly the listed fields and types. Exactness nests. It does not freeze the hash.
- Exact → compatible open is assignable. Open → exact is not.
- Builtin type names and alias names cannot be redefined.
- Aliases are not new runtime types.

## Common Mistakes

- Expecting open object aliases to reject extra fields
- Treating `exact` as immutability (`const` freezes; `exact` does not)
- Treating aliases as nominal runtime types

## Exact object example

```echo
type User = exact { id: int, name: str };
user: User = { id: 1, name: "Echo" };
```

Extra field → **E3208**. Missing field → **E3209**.

## See Also

- [Variables and Types](/getting-started/variables-and-types)
- [Functions](/getting-started/functions)
- [Hashes](/core-concepts/hashes)
