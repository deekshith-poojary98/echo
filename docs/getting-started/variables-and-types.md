# Variables and Types

Declare a type. Echo checks it at runtime when the value is bound or reassigned.

```echo
name: str = "Echo";
count: int = 1;
price: float = 2.5;
ok: bool = true;
value: dynamic = null;
const title: str = "Echo";
[a: int, b: int] = [1, 2];
{ id: int, name: str } = { id: 1, name: title };
{ id as userId: int } = { id: 1 };
{ id: int, rest: dynamic... } = { id: 1, extra: true };
```

```echo
title: str = "Echo";
users: int = 42;
ratio: float = 1.5;
enabled: bool = true;
missing: dynamic = null;

say(title, users, ratio, enabled, missing);
```

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

`const name: T = expression;` cannot be reassigned. The bound list or hash is frozen.

Destructuring unpacks a list or hash into names:

```echo
[a: int, b: int] = pair;
[a, b] = pair;
{ id: int, name: str } = user;
[head: int, rest: int...] = xs;
```

### Built-in types
- `int`: whole numbers
- `float`: decimal numbers
- `str`: text
- `bool`: `true` or `false`
- `dynamic`: any runtime value
- `list`: mutable ordered collection
- `hash`: mutable key-value map
- `void`: only `null` (used when a binding may be absent)
- `null`: literal value for missing data (typed as `dynamic` unless the binding is `void` or `dynamic`)

### Union types
```echo
type Id = int | str;
id: Id = 1;
id = "x";
fn show(x: int | str) -> str {
    return asString(x);
}
```

A value matches a union if it matches any member. Unions are not Option — Echo has no `null` type, so write `str | void` when `null` is allowed. Use `switch` type arms to dispatch on members.

### Classes (nominal)

```echo
class Point {
    new {
        x: int;
        y: int;
    }
}

p: Point = Point { x: 3, y: 4 };
say(p.x);
p.x = 10;
say(type(p)); // "Point"
```

`Point` is a nominal type — not the same as `exact { x: int, y: int }`. Fields are declared under **`new { ... }`** (optional defaults: `x: int = 0`). Construction requires every field without a default and rejects extras. Methods use an explicit `this` receiver: `fn length(this) -> int { ... }`, call `p.length()` or unbound `Point.length(p)`, and `p.length` / `Point.length` are function values. Interfaces declare method signatures only (`interface Named { fn name(this) -> str; }`); a class implements them by providing compatible methods (no `implements` clause).

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
