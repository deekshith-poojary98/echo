# Built-in Methods

## Overview
Echo exposes built-in functionality through standalone calls and method-call syntax.

## Syntax
```echo
say("Echo");
ask("Name: ");
"hello".upperCase();
nums.push(1);
user.ensure("name", "Echo");
```

## I/O
### `say(...)`
Print values separated by spaces.

```echo
say("Echo", true, null);
```

Output:
```text
Echo true null
```

### `ask(prompt)`
Read a line from standard input.

### `wait(seconds)`
Sleep for the given number of seconds.

## Conversion
### `asInt()`
### `asFloat()`
### `asBool()`
### `asString()`
### `type()`

```echo
say("42".asInt());
say(true.asString());
```

## Strings
### `trim()`
### `upperCase()`
### `lowerCase()`
### `length()`
### `reverse()`
### `format(...)`

```echo
say("  echo  ".trim());
say("echo".upperCase());
say("Hello, {}".format("Echo"));
```

## Lists
### `push(value)`
### `empty()`
### `clone()`
### `countOf(value)`
### `find(value)`
### `insertAt(index, value)`
### `pull([index])`
### `removeValue(value)`
### `order([comparator])`
### `merge(other)`

```echo
nums: list = [3, 1, 2];
nums.order();
say(nums);
```

## Hashes
### `keys()`
### `values()`
### `pairs()`
### `wipe()`
### `take(key)`
### `take_last()`
### `ensure(key, default)`
### `merge(other)`

```echo
user: hash = { name: "Echo" };
say(user.ensure("name", "fallback"));
say(user.keys());
```

## Notes
- Built-ins do not support keyword arguments.
- Some built-ins can be called as standalone functions or as methods.
- Mutating methods interact with `watch` and function scope rules.

## Common Mistakes
- Using keyword arguments with built-ins
- Passing non-string keys to hash methods that require keys
- Assuming `order()` accepts anything other than zero args or one comparator

## See Also
- [Lists](/core-concepts/lists)
- [Hashes](/core-concepts/hashes)
- [Operators](/reference/operators)
- [Language Reference](/reference/language-reference)
