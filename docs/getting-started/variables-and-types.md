# Variables and Types

## Overview
Variables in Echo are declared with explicit types, and those types are enforced at runtime.

## Syntax
```echo
name: str = "Echo";
count: int = 1;
price: float = 2.5;
ok: bool = true;
value: dynamic = null;
```

## Example
```echo
title: str = "Echo";
users: int = 42;
ratio: float = 1.5;
enabled: bool = true;
missing: dynamic = null;

say(title, users, ratio, enabled, missing);
```

## Output
```text
Echo 42 1.5 true null
```

## Notes
### Declaration
Use this form for a new variable:

```echo
name: Type = expression;
```

### Reassignment
Use this form after declaration:

```echo
name = expression;
```

### Built-in types
- `int`: whole numbers
- `float`: decimal numbers
- `str`: text
- `bool`: `true` or `false`
- `dynamic`: any runtime value
- `list`: mutable ordered collection
- `hash`: mutable key-value map
- `null`: literal value for missing data

### Runtime type checking
```echo
count: int = 1;
count = 2;      // valid
count = "two"; // runtime type error
```

## Common Mistakes
### Assigning before declaration
```echo
count = 1;
```

### Treating `null` as a type
```echo
x: null = null;
```

Use `dynamic` instead.

### Using `void` as a variable type
This is not allowed.

## Current Limitation
- No generics such as `list<int>`.
- Lists are not element-typed.
- Hashes are only structurally typed when used through object type aliases.

## See Also
- [Strings and Interpolation](/getting-started/strings-and-interpolation)
- [Lists](/core-concepts/lists)
- [Hashes](/core-concepts/hashes)
- [Type Aliases](/core-concepts/type-aliases)
