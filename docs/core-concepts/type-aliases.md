# Type Aliases

## Overview
Echo supports named aliases for built-in types and object-shaped aliases for hashes.

## Syntax
```echo
type Age = int;
type User = { id: int, name: str, active: bool };
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
- Object aliases check that required fields exist and match declared field types.
- Built-in type names cannot be redefined.
- Alias names cannot be redefined.

## Common Mistakes
- Assuming object aliases reject extra fields
- Treating aliases as new runtime types

## Current Limitation
Object aliases validate required fields but do not reject additional fields.

## See Also
- [Variables and Types](/getting-started/variables-and-types)
- [Functions](/getting-started/functions)
- [Hashes](/core-concepts/hashes)
