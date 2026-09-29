# Variables and Types

Declare a type. Echo checks it at runtime when the value is bound or reassigned.

## Basic Example

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

## How It Works

### Declaration

```echo
name: Type = expression;
```

### Reassignment

```echo
name = expression;
```

`const name: T = expression;` cannot be reassigned. The bound list or hash is frozen.

### Destructuring

Each of these is a complete program:

```echo
const title: str = "Echo";
[a: int, b: int] = [1, 2];
{ id: int, label: str } = { id: 1, label: title };
say(a, b, id, label);
```

#### Output

```text
1 2 1 Echo
```

```echo
{ id as userId: int } = { id: 1 };
say(userId);
```

#### Output

```text
1
```

```echo
{ id: int, rest: dynamic... } = { id: 1, extra: true };
say(id);
say(rest);
```

#### Output

```text
1
{"extra": true}
```

Untyped forms also work when the right-hand side is already checked:

```echo
pair: list = [1, 2];
[a, b] = pair;
say(a, b);
```

### Built-in types

- `int`: whole numbers (arbitrary precision)
- `float`: decimal numbers
- `str`: text
- `bool`: `true` or `false`
- `dynamic`: any runtime value (including `null`)
- `list`: mutable ordered collection
- `hash`: mutable key-value map
- `void`: only valid as a **function return** annotation, or as a **union member** (`str | void`) when `null` is allowed — not as a standalone variable type

`null` is a **value**, not a type name.

### Union types

```echo
type Id = int | str;
id: Id = 1;
id = "x";
fn show(x: int | str) -> str {
    return asString(x);
}
say(show(id));
```

#### Output

```text
x
```

A value matches a union if it matches any member. Unions are not Option — Echo has no `null` type, so write `str | void` when `null` is allowed:

```echo
x: str | void = null;
say(x);
```

#### Output

```text
null
```

Use `switch` type arms to dispatch on members.

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
say(type(p));
```

#### Output

```text
3
Point
```

`Point` is a nominal type — not the same as `exact { x: int, y: int }`. Fields are declared under **`new { ... }`** (optional defaults: `x: int = 0`). Construction requires every field without a default and rejects extras. Methods use an explicit `this` receiver: `fn length(this) -> int { ... }`, call `p.length()` or unbound `Point.length(p)`; type methods omit `this` (`fn origin() -> Point`, call `Point.origin()`). Interfaces declare method signatures only (`interface Named { fn name(this) -> str; }`); a class implements them by providing compatible methods; an optional `implements Named` clause documents intent and is checked (**E3214**).

### Runtime type checking

```echo
count: int = 1;
count = 2;      // valid
// count = "two"; // runtime type error
say(count);
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

Use `dynamic` or a union such as `str | void` instead.

### Using `void` alone as a variable type

```echo
x: void = null;
```

That is a syntax error. Prefer `x: str | void = null;` or `x: dynamic = null;`.

### Redeclaring a name in one program — E1001

```echo
name: str = "Echo";
{ id: int, name: str } = { id: 1, name: "Ada" };
```

Fails with **E1001** because `name` is already declared. Use a different binding name, or assign without a type after the first declaration.

## Current Limitation

- No generics such as `list<int>`.
- Lists are not element-typed.
- Hashes are only structurally typed when used through object type aliases.

## Related

- [Strings and Interpolation](/getting-started/strings-and-interpolation)
- [Lists](/core-concepts/lists)
- [Hashes](/core-concepts/hashes)
- [Type Aliases](/core-concepts/type-aliases)
