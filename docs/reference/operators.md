# Operators

## Overview
This page lists Echo's current operators and their behavior.

## Syntax
```echo
+  -  *  /  %
== != < > <= >=
&& || !
=
```

## Arithmetic
- `+`
- `-`
- `*`
- `/`
- `%`

### Integer division
If both operands are `int`, `/` returns an `int` truncated toward zero.

```echo
say(7 / 3);
say(7 / -3);
```

Output:
```text
2
-2
```

### Integer modulo
`int % int` follows truncation-toward-zero semantics.

## Comparison
- `==`
- `!=`
- `<`
- `>`
- `<=`
- `>=`

## Logical
- `&&`
- `||`
- `!`

`&&` and `||` short-circuit.

## Assignment
- `=`
- `arr[i] = value;`
- `grid[r][c] = value;`

## Notes
- Unary minus is supported.
- There are no compound assignment operators like `+=`.

## See Also
- [Variables and Types](/getting-started/variables-and-types)
- [Loops Reference](/reference/loops-reference)
- [Language Reference](/reference/language-reference)
