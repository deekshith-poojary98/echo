# Strings and Interpolation

Quotes, escapes, `${...}` interpolation, and `format` (positional + named).

```echo
name: str = "Echo";
message: str = "Hello, ${name}!";
formatted: str = "Score: {}".format(42);
named: str = "Score: {score}".format({ score: 42 });
```

```echo
name: str = "Echo";
count: int = 5;
ok: bool = true;
missing: dynamic = null;

say("Name: ${name}");
say("Count: ${count}");
say("OK: ${ok}");
say("Missing: ${missing}");
say("Hello, {}!".format(name));
say("Hello, {who}!".format({ who: name }));
```

```text
Name: Echo
Count: 5
OK: true
Missing: null
Hello, Echo!
Hello, Echo!
```

## Notes
### Quotes
Both styles work:

```echo
a: str = "Echo";
b: str = 'Echo';
```

Triple quotes may span lines and still interpolate:

```echo
block: str = """
hello ${name}
""";
```

### Escapes
Supported escapes:

```text
\\
\"
\'
\n
\t
\r
```

### Interpolation
Interpolation uses Echo-style output rules, so booleans print as `true` and `false`, and `null` prints as `null`.

### `format(...)`
Supported placeholders:

```text
{}
{0}
{1}
{name}
{{
}}
```

Named placeholders take values from a trailing hash:

```echo
say("Hello, {name}!".format({ name: "Echo" }));
say("{0} scored {points}".format("Ada", { points: 42 }));
```

## Common Mistakes
### Missing closing brace in interpolation
```echo
say("Hello ${name");
```

### Expecting advanced formatting like width or precision
This is not supported.

### Assuming single quotes are raw strings
Echo still processes escapes and interpolation tokenization.

### Named placeholder without a trailing hash
```echo
say("{name}".format("Echo"));  // error — pass { name: "Echo" }
```

## Current Limitation
- `format()` has no width / precision / alignment specs.
- No raw string syntax.
- Invalid characters inside ``${...}`` may fail later than expected.

## See Also
- [Variables and Types](/getting-started/variables-and-types)
- [Built-in Methods](/standard-library/built-in-methods)
- [Known Limitations](/errors-diagnostics/known-limitations)
