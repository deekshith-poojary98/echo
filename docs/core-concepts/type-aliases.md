# Type Aliases

## Overview
Echo supports named aliases for built-in types and object-shaped aliases for hashes.

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

## Output
```text
{"id": 1, "name": "Echo", "active": true}
```

## Notes
- Aliases can be used in variable declarations and function parameters.
- Open object aliases check required fields and types but allow additional fields.
- `exact { ... }` aliases require exactly the listed fields and types. Exactness nests and does not freeze the hash.
- Exact objects are assignable to compatible open object types; open objects are not assignable to exact types.
- Built-in type names cannot be redefined.
- Alias names cannot be redefined.

## Common Mistakes
- Assuming open object aliases reject extra fields
- Assuming `exact` makes a hash immutable
- Treating aliases as new runtime types

## Exact object example
```echo
type User = exact { id: int, name: str };
user: User = { id: 1, name: "Echo" };
```

An extra field reports **E3208**; a missing field reports **E3209**.

## See Also
- [Variables and Types](/getting-started/variables-and-types)
- [Functions](/getting-started/functions)
- [Hashes](/core-concepts/hashes)
