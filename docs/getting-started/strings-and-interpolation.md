# Strings and Interpolation

## Overview
Echo strings support quotes, escapes, interpolation, and positional formatting.

## Syntax
```echo
name: str = "Echo";
message: str = "Hello, ${name}!";
formatted: str = "Score: {}".format(42);
```

## Example
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
```

## Output
```text
Name: Echo
Count: 5
OK: true
Missing: null
Hello, Echo!
```

## Notes
### Quotes
Both styles work:

```echo
a: str = "Echo";
b: str = 'Echo';
```

### Escapes
Supported escapes:

```text
\\
\"
\'
\n
	
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
{{
}}
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

## Current Limitation
- `format()` only supports positional placeholders.
- No named formatting.
- No raw string syntax.
- Invalid characters inside ``${...}`` may fail later than expected.

## See Also
- [Variables and Types](/getting-started/variables-and-types)
- [Built-in Methods](/standard-library/built-in-methods)
- [Known Limitations](/errors-diagnostics/known-limitations)
