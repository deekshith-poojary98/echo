# Built-in Methods

## Overview
Echo exposes built-in functionality through standalone function calls and method-call syntax on values. Most conversion and utility built-ins can be called either way.

```echo
say("Echo");
"hello".upperCase();
nums.push(1);
user.ensure("name", "Echo");
```

> **Note:** Variadic built-ins (`say`, `eprint`, `format`, `pathJoin`) do not support keyword arguments. All other built-ins accept keyword arguments by parameter name, matching how user-defined functions work.

---

## I/O

### `say(...)`
Prints one or more values to stdout, separated by spaces, followed by a newline. Accepts any type.

```echo
say("Echo", true, null);
say([1, 2, 3]);
```

Output:
```text
Echo true null
[1, 2, 3]
```

---

### `eprint(...)`
Same as `say`, but writes to stderr. Variadic. No keyword arguments.

```echo
eprint("missing file");
```

---

### `ask(prompt)`
Displays `prompt` and reads a line of text from stdin. Returns the input as a `str`.

```echo
name: str = ask("Enter your name: ");
say("Hello,", name);
```

Output:
```text
Enter your name: Ada
Hello, Ada
```

---

### `readLine()`
Reads one line from stdin with no required prompt. EOF aborts with an Echo error. Takes no arguments.

```echo
line: str = readLine();
```

---

### `wait(seconds)`
Pauses execution for the given number of seconds. Accepts `int` or `float`.

```echo
say("Starting...");
wait(2);
say("Done.");
```

---

## Conversion

### `asInt()`
Converts the value to an `int`. Can be called as a method or standalone.
`bool`, `null`, lists, hashes, and non-integer strings are type errors.

```echo
n: int = "42".asInt();
say(n + 1);        // 43
say(asInt(3.9));   // 3
```

---

### `asFloat()`
Converts the value to a `float`.

```echo
f: float = "3.14".asFloat();
say(f);            // 3.14
say(asFloat(7));   // 7.0
```

---

### `asBool()`
Converts the value to a `bool` using Python truthiness rules (`0`, `""`, `null`, `[]`, `{}` are falsy).

```echo
say(0.asBool());      // false
say("hi".asBool());   // true
say(asBool(null));    // false
```

---

### `asString()`
Converts the value to a `str` using Echo's stringification rules (`true`/`false`/`null` are lowercase, nested strings in lists/hashes are quoted).

```echo
say(true.asString());      // true
say(42.asString());        // 42
say([1, 2].asString());    // [1, 2]
```

---

### `type()`
Returns the Echo type name of the value as a `str`. Possible values: `"int"`, `"float"`, `"str"`, `"bool"`, `"list"`, `"hash"`, `"dynamic"`.

```echo
say(42.type());           // int
say("hello".type());      // str
say([].type());           // list
say(type(true));          // bool
```

---

### `default(fallback)`
Returns the value itself if it is truthy; otherwise returns `fallback`. Uses Python truthiness.

```echo
x: dynamic = null;
say(x.default("guest"));    // guest

y: int = 5;
say(y.default(0));          // 5
```

---

## Host

These talk to the process, not new language syntax. They abort with Echo errors.

### `args()`
Returns the program argument list as `str` values. Does not include the source path or interpreter flags such as `--plain`.

```echo
foreach flag: str in args() {
    say(flag);
}
```

```bash
echo app.echo --plain -- input.txt --verbose
```

### `env(name)` / `envOr(name, fallback)`
`env` returns the named environment variable or aborts if it is unset. An empty value counts as set. `envOr` returns `fallback` when the name is unset.

```echo
home: str = env("HOME");
city: str = envOr("CITY", "unknown");
```

### `readFile(path)` / `writeFile(path, contents)`
UTF-8 text only. Relative paths use the process working directory. Missing files, permission errors, and invalid UTF-8 abort. The playground host denies both.

```echo
text: str = readFile("notes.txt");
writeFile("out.txt", text);
```

### `fileExists(path)`
Returns `true` when `path` is an existing file. Missing paths and directories are `false`. Does not abort when the file is missing. A host that denies files (playground) still aborts.

```echo
if fileExists("notes.txt") {
    say(readFile("notes.txt"));
}
```

### `cwd()`
Returns the host working directory as a string. Relative file paths resolve against this directory. Takes no arguments.

```echo
say(cwd());
```

### `exit(code)`
Stops the program. `code` must be an integer (`bool` is a type error). The process returns that code. Success and failure both print nothing extra; earlier `say` output is kept.

```echo
if !fileExists("notes.txt") {
    say("missing notes");
    exit(1);
}
```

### `isDir(path)`
Returns `true` when `path` is an existing directory. Missing paths and files are `false`. A host that denies files still aborts.

```echo
say(isDir("out"));
```

### `listFiles(path)`
Returns a sorted list of names in that directory, including files and subdirectories. Missing paths and non-directories abort. The playground host denies this.

```echo
foreach name: str in listFiles(".") {
    say(name);
}
```

### `mkdir(path)`
Creates the leaf directory only. Does not create missing parents. Existing directories and a file in the way abort. The playground host denies this.

```echo
mkdir("out");
```

### `removeFile(path)`
Deletes a file. Missing paths and directories abort. The playground host denies this.

```echo
removeFile("scratch.txt");
```

### `copyFile(src, dest)`
Copies a file as bytes. Not a directory copy. Missing source and missing dest parent abort. Existing dest files are overwritten; dest directories abort. The playground host denies this.

```echo
copyFile("src.bin", "dest.bin");
```

### `pathJoin(...)`
Joins 2+ string parts with pathlib (not string concat). Variadic like `say`. No keyword arguments. Does not need file access, so the playground keeps it.

```echo
say(pathJoin("a", "b", "c"));
```

### `run(command, args)`
Runs `command` with a list of string arguments. Empty `args` is allowed. Does not use a shell. Returns a hash `{ "code": int, "stdout": str, "stderr": str }`. A non-zero process code is returned, not raised. Missing executables abort. The playground host denies this (`allow_run=False`).

```echo
proc: hash = run("true", []);
say(proc["code"]);
```

### `now()`
Returns the current unix time as an `int` number of seconds. Takes no arguments.

```echo
stamp: int = now();
```

### `assert(cond, message)`
Aborts with an Echo error when `cond` is falsy. `message` must be a `str`. Truthy values continue.

```echo
assert(fileExists("notes.txt"), "missing notes");
```

### `parseJson(text)` / `writeJson(value)`
JSON objects become hashes, arrays become lists, whole numbers become `int`, other finite numbers become `float`. Invalid JSON and non-finite floats abort.

```echo
data: dynamic = parseJson("{\"n\": 1}");
say(writeJson(data));
```

---

## Strings

### `trim()`
Returns a new string with leading and trailing whitespace removed.

```echo
say("  echo  ".trim());    // echo
```

---

### `upperCase()`
Returns a new string with all characters converted to uppercase.

```echo
say("hello".upperCase());    // HELLO
```

---

### `lowerCase()`
Returns a new string with all characters converted to lowercase.

```echo
say("ECHO".lowerCase());    // echo
```

---

### `length()`
Returns the number of characters in a string, or the number of elements in a list.

```echo
say("Echo".length());         // 4
say([1, 2, 3].length());      // 3
```

---

### `reverse()`
On a string, returns a new reversed string. On a list, reverses the list **in place** and returns it.

```echo
say("echo".reverse());        // ohce

nums: list = [1, 2, 3];
nums.reverse();
say(nums);                    // [3, 2, 1]
```

---

### `split(separator)`
Splits a string on a non-empty separator and returns a list of strings.

```echo
say("a,b,c".split(","));    // [a, b, c]
```

### `replace(old, new)`
Replaces every non-overlapping occurrence of `old` with `new`. `old` must be a non-empty string.

```echo
say("foo foo".replace("foo", "bar"));    // bar bar
```

### `contains(part)`
On a string, reports whether `part` occurs. On a list, reports whether a value is present using Echo `==`. Empty string `part` is `true`.

```echo
say("echo".contains("ch"));    // true
say([1, 2].contains(2));       // true
```

### `slice(start, end)`
Returns a new string or list from `start` up to but not including `end`. Both bounds must be integers in range. `slice(0, value.length())` copies the whole sequence.

```echo
say("Echo".slice(1, 3));       // ch
say([1, 2, 3, 4].slice(1, 3)); // [2, 3]
```

### `startsWith(prefix)` / `endsWith(suffix)`
Reports whether a string begins or ends with the given string. The argument must be a string. An empty prefix or suffix is `true`.

```echo
say("echo".startsWith("ec"));    // true
say("echo".endsWith("ho"));      // true
```

### `indexOf(part)` / `lastIndexOf(part)`
Returns the first or last index of `part` in a string, or `-1` if it is missing. `part` must be a string. An empty `part` is `0` / the string length.

```echo
say("echo echo".indexOf("ch"));         // 1
say("echo echo".lastIndexOf("echo"));   // 5
say("echo".indexOf("x"));               // -1
```

### `repeat(n)`
Repeats the string `n` times. `n` must be a non-negative integer (`bool` is a type error).

```echo
say("ab".repeat(3));    // ababab
```

### `padStart(width, fill)` / `padEnd(width, fill)`
Pads the string to `width` using `fill`. `width` must be a non-negative integer. `fill` must be a non-empty string and is repeated as needed. If the string is already at least `width`, the original is returned.

```echo
say("5".padStart(3, "0"));    // 005
say("5".padEnd(3, "0"));      // 500
```

### `replaceFirst(old, new)`
Replaces the first non-overlapping occurrence of `old` with `new`. `old` must be a non-empty string.

```echo
say("foo foo".replaceFirst("foo", "bar"));    // bar foo
```

### `join(separator)`
Joins a list of strings with `separator` and returns a string. `separator` may be empty. An empty list is `""`. Non-string items or a non-string separator are type errors.

```echo
say(["a", "b", "c"].join(","));    // a,b,c
say(join(["x", "y"], ""));         // xy
```

### `format(...)`
Performs template string substitution. Use `{}` for sequential placeholders or `{0}`, `{1}`, ... for positional ones. To include literal braces, use doubled braces in the format template.

```echo
say("Hello, {}!".format("Echo"));           // Hello, Echo!
say("{0} + {1} = {2}".format(1, 2, 3));    // 1 + 2 = 3
say("{{literal braces}}".format());         // {literal braces}
```

---

## Numbers

### `abs(n)`
Returns the absolute value. `n` must be `int` or `float` (`bool` is a type error). An `int` stays an `int`; a `float` stays a `float`.

```echo
say(abs(-3));      // 3
say(abs(-3.5));    // 3.5
```

### `min(a, b)` / `max(a, b)`
Returns the lesser or greater of two numbers. Mixed `int` / `float` is allowed. `bool` is a type error.

```echo
say(min(2, 5));      // 2
say(max(2, 5));      // 5
say(min(1.5, 1));    // 1
```

### `floor(n)` / `ceil(n)`
Rounds toward `-∞` or `+∞` and returns an `int`. `n` must be `int` or `float` (`bool` is a type error).

```echo
say(floor(3.2));     // 3
say(ceil(3.2));      // 4
say(floor(-3.2));    // -4
```

### `random()`
Returns a `float` in `[0, 1)`. Takes no arguments.

```echo
n: float = random();
```

### `randomInt(min, max)`
Inclusive integer in `[min, max]`. Both bounds are `int` (not `bool`). `min` must be `<= max`.

```echo
n: int = randomInt(1, 6);
```

---

## Lists

### `push(value)`
Appends `value` to the end of the list. Mutates the list in place.

```echo
nums: list = [1, 2];
nums.push(3);
say(nums);    // [1, 2, 3]
```

---

### `insertAt(index, value)`
Inserts `value` at the given `index`, shifting subsequent elements right. Valid indexes are `0` through `list.length()`.

```echo
nums: list = [1, 3];
nums.insertAt(1, 2);
say(nums);    // [1, 2, 3]
```

---

### `pull([index])`
Removes and returns the element at `index`. If `index` is omitted, removes and returns the last element. Raises an error if the list is empty.

```echo
nums: list = [1, 2, 3];
last: int = nums.pull();
say(last);    // 3
say(nums);    // [1, 2]

first: int = nums.pull(0);
say(first);   // 1
```

---

### `removeValue(value)`
Removes the first occurrence of `value` from the list. Does nothing if `value` is not found.

```echo
items: list = [1, 2, 3, 2];
items.removeValue(2);
say(items);    // [1, 3, 2]
```

---

### `empty()`
Removes all elements from the list, leaving it empty. Mutates in place.

```echo
nums: list = [1, 2, 3];
nums.empty();
say(nums);    // []
```

---

### `find(value)`
Returns the index of the first occurrence of `value` in the list, or `-1` if the value is not found.

```echo
nums: list = [10, 20, 30];
say(nums.find(20));    // 1
say(nums.find(99));    // -1
```

Standalone keyword form:

```echo
nums: list = [10, 20, 30];
say(find(items: nums, value: 20));    // 1
```

---

### `countOf(value)`
Returns the number of times `value` appears in the list.

```echo
items: list = [1, 2, 1, 3, 1];
say(items.countOf(1));    // 3
```

Standalone keyword form:

```echo
items: list = [1, 2, 1, 3, 1];
say(countOf(items: items, value: 1));    // 3
```

---

### `order([comparator])`
Sorts the list **in place** in ascending order by default. Optionally accepts a comparator function that takes two arguments and returns a negative `int` (first before second), `0` (equal), or positive `int` (first after second).

```echo
nums: list = [3, 1, 2];
nums.order();
say(nums);    // [1, 2, 3]
```

```echo
fn descending(a: int, b: int) -> int {
    return b - a;
}

nums: list = [3, 1, 2];
nums.order(descending);
say(nums);    // [3, 2, 1]
```

---

### `clone()`
Returns a **shallow** copy of the list. Modifications to the clone do not affect the original, but nested objects are shared.

```echo
a: list = [1, 2, 3];
b: list = a.clone();
b.push(4);
say(a);    // [1, 2, 3]
say(b);    // [1, 2, 3, 4]
```

---

### `merge(other)` *(list)*
Extends the list in place by appending all elements from `other` (a list or string).

```echo
a: list = [1, 2];
b: list = [3, 4];
a.merge(b);
say(a);    // [1, 2, 3, 4]
```

---

## Hashes

### `has(key)`
Returns `true` if the hash has `key`. The key must be a `str`.

```echo
say({ name: "Ada" }.has("name"));    // true
```

### `keys()`
Returns a list of all keys in insertion order.

```echo
user: hash = { name: "Ada", role: "admin" };
say(user.keys());    // [name, role]
```

---

### `values()`
Returns a list of all values in insertion order.

```echo
user: hash = { name: "Ada", role: "admin" };
say(user.values());    // [Ada, admin]
```

---

### `pairs()`
Returns a list of `[key, value]` pairs in insertion order.

```echo
user: hash = { name: "Ada", score: 99 };
say(user.pairs());    // [[name, Ada], [score, 99]]
```

---

### `ensure(key, default)`
If `key` does not exist in the hash, sets it to `default` and returns `default`. If `key` already exists, returns its current value without modifying it. Useful for counters and bucket building.

```echo
counts: hash = {};
counts["a"] = counts.ensure("a", 0) + 1;
counts["a"] = counts.ensure("a", 0) + 1;
say(counts);    // {"a": 2}
```

---

### `take(key)`
Removes the entry with `key` from the hash and returns `[key, value]` as a list.

```echo
user: hash = { name: "Ada", temp: true };
removed: list = user.take("temp");
say(removed);    // [temp, true]
say(user);       // {"name": "Ada"}
```

---

### `take_last()`
Removes the most recently inserted key-value pair and returns `[key, value]` as a list.

```echo
h: hash = { a: 1, b: 2, c: 3 };
last: list = h.take_last();
say(last);    // [c, 3]
say(h);       // {"a": 1, "b": 2}
```

---

### `wipe()`
Removes all entries from the hash, leaving it empty. Mutates in place.

```echo
h: hash = { a: 1, b: 2 };
h.wipe();
say(h);    // {}
```

---

### `merge(other)` *(hash)*
Copies all key-value pairs from `other` into the hash, overwriting any existing keys. Mutates in place.

```echo
a: hash = { x: 1, y: 2 };
b: hash = { y: 99, z: 3 };
a.merge(b);
say(a);    // {"x": 1, "y": 99, "z": 3}
```

---

### `clone()` *(hash)*
Returns a **shallow** copy of the hash.

```echo
original: hash = { name: "Ada" };
copy: hash = original.clone();
copy["name"] = "Echo";
say(original["name"]);    // Ada
say(copy["name"]);        // Echo
```

---

## Notes
- All built-ins except `say`, `eprint`, and `format` support keyword arguments by parameter name — the same way user-defined functions do.
- For standalone `find(...)` and `countOf(...)` calls, use `items:` for the collection argument.
- Most conversion built-ins (`asInt`, `asFloat`, `asBool`, `asString`, `type`) work as both standalone functions and method calls.
- Mutating list/hash methods (`push`, `pull`, `order`, `wipe`, etc.) interact with `watch` and function scope rules.
- `clone()` is **shallow** for both lists and hashes.

## Common Mistakes
- Using keyword arguments with built-ins
- Passing non-string keys to hash indexing or hash methods
- Calling `pull()` on an empty list
- Assuming `order()` accepts more than one comparator
- Expecting `clone()` to deep-copy nested structures

## See Also
- [Lists](/core-concepts/lists)
- [Hashes](/core-concepts/hashes)
- [Operators](/reference/operators)
- [Language Reference](/reference/language-reference)
