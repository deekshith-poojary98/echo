# Classes and Interfaces

Nominal classes, `new { ... }` fields, methods, properties, and interfaces.

```echo
interface Named {
    fn name(this) -> str;
}

class Point {
    new {
        x: int = 0;
        y: int = 0;
    }

    fn origin() -> Point {
        return Point {};
    }

    fn length(this) -> int {
        return this.x * this.x + this.y * this.y;
    }
}

class Counter {
    new {
        priv n: int = 0;
    }

    get count(this) -> int {
        return this.n;
    }

    set count(this, value: int) {
        this.n = value;
    }
}

class User implements Named {
    new {
        label: str;
    }

    fn name(this) -> str {
        return this.label;
    }
}

fn show(n: Named) {
    say(n.name());
}

p: Point = Point.origin();
say(Point.length(Point { x: 3, y: 4 }));
c: Counter = Counter {};
c.count = 7;
say(c.count);
show(User { label: "Ada" });
```

```text
25
7
Ada
```

Runnable copy: `examples/classes_and_interfaces.echo` (Point / User); properties shown above.

## Notes

- Fields live under **`new { ... }`**. Defaults let callers omit fields (`Point {}`).
- Instance methods take **`this`**; type methods omit it (`Point.origin()`).
- Unbound form: **`Point.length(p)`**.
- Properties: **`get name(this)`** / **`set name(this, value: T)`** — access as `obj.name` / `obj.name = v` (0.9.5). Soft keywords; `fn set` still works as a method name.
- **`implements`** is optional; inference still assigns matching classes to interfaces. Properties do not satisfy interface methods.
- No class inheritance — use interfaces and composition.

## See Also

- [Variables and Types](/getting-started/variables-and-types)
- [Language Reference](/reference/language-reference)
- [Known Limitations](/errors-diagnostics/known-limitations)
