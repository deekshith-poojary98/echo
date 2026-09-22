# Operators

Current operators and how they behave.

## Syntax

```echo
+  -  *  /  %
== != < > <= >=
&& || !
=
+= -= *= /= %=
```

## Arithmetic

- `+` `-` `*` `/` `%`
- Unary `-` is supported
- `"a" + "b"` and `[1] + [2]` concatenate; mixed `str + int` is a type error

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

`int % int` follows truncation-toward-zero. Division or modulo by zero aborts.

## Comparison

- `==` `!=` `<` `>` `<=` `>=`
- `true == 1` is `false`
- Lists and hashes compare structurally

## Logical

- `&&` `||` `!`
- `&&` and `||` short-circuit

## Assignment

- `=`
- Compound: `+=` `-=` `*=` `/=` `%=` (same type and mutability rules as `x = x + y`; also on class fields: `this.x += 1`)
- `arr[i] = value;`
- `grid[r][c] = value;`

`const` bindings reject reassignment and compound assign (**E3201**).

## Type unions

In type position, `|` joins members (`int | str`). `||` stays boolean or. See the language semantics contract.

## See Also

- [Variables and Types](/getting-started/variables-and-types)
- [Loops Reference](/reference/loops-reference)
- [Language Reference](/reference/language-reference)
