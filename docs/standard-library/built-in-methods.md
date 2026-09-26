# Built-in Methods

Standalone calls and method form on values. Most conversion and utility builtins work either way.

```echo
say("Echo");
"hello".upperCase();
nums.push(1);
user.ensure("name", "Echo");
```

Variadic builtins (`say`, `eprint`, `format`, `pathJoin`) do not take keyword arguments. Other builtins accept kwargs by parameter name, same as user `fn`s.

**Values (0.7.3):** a bare builtin name is a function value (`print: fn(str) -> dynamic = say;`, `xs.map` without `()`). `type(say)` is `"fn"`. Variadics are `fn(dynamic...) -> void` (`say`, `eprint`) or `fn(dynamic...) -> str` (`format`, `pathJoin`). Equality is the same builtin; bound methods also need the same receiver. Host-denied builtins are still values; **calling** them still aborts.

---

## I/O

### `say(...)`
Writes values to stdout, space-separated, with a trailing newline. Any type.

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
Prints `prompt`, reads one stdin line, returns `str`.

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
Sleeps that many seconds. `int` or `float`.

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

### `asIntOr(fallback)`
Same conversion as `asInt`, but unparseable strings, `null`, lists, and hashes return `fallback`. `bool` is still a type error. `asInt` still aborts.

```echo
n: int = asIntOr("abc", 0);    // 0
say(" 42 ".asIntOr(0));        // 42
```

---

### `asFloat()`
Converts the value to a `float`.

```echo
f: float = "3.14".asFloat();
say(f);            // 3.14
say(asFloat(7));   // 7.0
```

### `asFloatOr(fallback)`
Same conversion as `asFloat`, but unparseable strings, `null`, lists, and hashes return `fallback`. `bool` is still a type error. `asFloat` still aborts.

```echo
f: float = asFloatOr("nope", 0.0);    // 0.0
say("3.5".asFloatOr(0.0));            // 3.5
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

### `readFile(path)` / `readFileOr(path, fallback)` / `writeFile(path, contents)`
UTF-8 text only. Relative paths use the process working directory. Missing files, permission errors, and invalid UTF-8 abort `readFile`. `readFileOr` returns `fallback` for those expected read failures (including a directory path). The playground host denies both; a non-string path is a type error.

```echo
text: str = readFile("notes.txt");
maybe: str = readFileOr("notes.txt", "");
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

### `mkdirAll(path)`
Creates the directory and any missing parents (`mkdir -p`). An existing directory is a no-op success. A file in the way aborts. The playground host denies this.

```echo
mkdirAll("out/nested/deep");
```

### `removeFile(path)`
Deletes a file. Missing paths and directories abort. The playground host denies this.

```echo
removeFile("scratch.txt");
```

### `removeTree(path)`
Deletes a file or an entire directory tree. Missing paths abort. The playground host denies this.

```echo
removeTree("out");
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

### `httpGet(url)` / `httpPost(url, body)`
HTTP request helpers. Return a hash `{ "status": int, "body": str, "headers": hash }`. `url` and `body` are strings. Optional trailing `headers` hash (string → string). Non-2xx responses still return the hash. Network failures and bad types abort (**E2852**). The playground host denies these (`allow_http=False` → **E2801**).

```echo
resp: hash = httpGet("https://example.com/", { Accept: "application/json" });
say(resp["status"]);
created: hash = httpPost("https://example.com/items", "hello", { "Content-Type": "text/plain" });
```

### `httpGetOr(url, fallback)` / `httpPostOr(url, body, fallback)`
Same requests as `httpGet` / `httpPost`, but network failures (**E2852** runtime) return `fallback` instead of aborting. Optional trailing `headers` hash. Host deny (**E2801**) and type errors still abort.

```echo
resp: dynamic = httpGetOr("https://example.com/", { status: 0, body: "", headers: {} });
```

### `httpOk(status|resp)` / `httpRedirect(status|resp)`
`true` when the status is 2xx or 3xx. Accepts an `int` status or a response hash with an `int` `status` field.

```echo
if (httpOk(resp)) {
    say(resp["body"]);
}
```

### `now()`
Returns the current unix time as an `int` number of seconds. Takes no arguments.

```echo
stamp: int = now();
```

### `formatTime(secs, pattern)` / `parseTime(text, pattern)`
UTC format and parse for unix seconds. Patterns use Python `strftime` / `strptime`. Naive parse results are treated as UTC. No date object type and no local-timezone calendars.

```echo
stamp: int = parseTime("2020-01-02T03:04:05Z", "%Y-%m-%dT%H:%M:%SZ");
say(formatTime(stamp, "%Y-%m-%d"));
say(stamp.formatTime("%H:%M"));
```

Bad types or invalid text/pattern → **E2851**.

### `days(n)` / `hours(n)` / `minutes(n)`
Duration helpers that return seconds as `int`. `n` must be an `int`.

```echo
later: int = now() + hours(2) + minutes(30);
say(days(1));   // 86400
```

### `assert(cond, message)`
Aborts with an Echo error when `cond` is falsy. `message` must be a `str`. Truthy values continue.

```echo
assert(fileExists("notes.txt"), "missing notes");
```

### `expect(cond, message)`
`cond` must be a `bool`. `message` must be a `str`. Under `echo test`, a false condition records failure **E2826** and the unit continues. Outside `echo test` it aborts like `assert`. Type errors (non-bool condition, non-string message) always abort.

```echo
expect(1 + 1 == 2, "add");
```

### `expectEq(left, right, message)` / `expectNeq(left, right, message)`
Compare with Echo `==`. `message` must be a `str`. Mismatch (or unexpected equality) records **E2827** / **E2828** and continues under `echo test`; outside `echo test` it aborts. The diagnostic includes `expected …, got …`.

```echo
expectEq(1 + 1, 2, "add");
expectNeq("a", "b", "distinct");
```

### `fail(message)`
Always aborts with an Echo error. `message` must be a `str`. Same diagnostic shape as `assert` (code `E2825`). Not recoverable. No `*Or` twin.

```echo
fail("unsupported shape");
```

### `parseJson(text)` / `parseJsonOr(text, fallback)` / `writeJson(value)`
JSON objects become hashes, arrays become lists, whole numbers become `int`, other finite numbers become `float`. Invalid JSON and non-finite floats abort `parseJson`. `parseJsonOr` returns `fallback` for invalid JSON. Non-string text is a type error for both.

```echo
data: dynamic = parseJson("{\"n\": 1}");
maybe: dynamic = parseJsonOr("{", null);
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
Returns a new string or list from `start` up to but not including `end`. Both bounds must be integers in range. `slice(0, value.length())` copies the whole sequence. Slice syntax matches that: `xs[1:3]`, `xs[1:]`, `xs[:3]`, and `xs[:]` (omitted start is `0`, omitted end is `length`).

```echo
say("Echo".slice(1, 3));       // ch
say([1, 2, 3, 4].slice(1, 3)); // [2, 3]
say([1, 2, 3, 4][1:3]);        // [2, 3]
say([1, 2, 3, 4][1:]);         // [2, 3, 4]
say([1, 2, 3, 4][:2]);         // [1, 2]
say([1, 2, 3, 4][:]);          // [1, 2, 3, 4]
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

### `regexMatch(pattern)` / `regexFind(pattern)` / `regexReplace(pattern, replacement)` / `regexSplit(pattern)`
Thin Python-`re` wrappers for scripting. Patterns are strings. Invalid patterns abort (**E2850**).

- `regexMatch` — `true` if the pattern matches anywhere
- `regexFind` — first match as a string, or `null`
- `regexReplace` — replace all matches; backrefs like `\1` work in the replacement
- `regexSplit` — split into a list of strings

```echo
say(regexMatch("hello 42", "\\d+"));           // true
say(regexFind("hello 42", "\\d+"));            // 42
say(regexReplace("a1b2", "\\d", "X"));         // aXbX
say(regexSplit("a,b,c", ","));                 // ["a", "b", "c"]
say("abc123".regexFind("[0-9]+"));             // 123
```

### `join(separator)`
Joins a list of strings with `separator` and returns a string. `separator` may be empty. An empty list is `""`. Non-string items or a non-string separator are type errors.

```echo
say(["a", "b", "c"].join(","));    // a,b,c
say(join(["x", "y"], ""));         // xy
```

### `format(...)`
Performs template string substitution. Use `{}` for sequential placeholders, `{0}`, `{1}`, ... for positional ones, or `{name}` for named ones filled from a trailing hash. To include literal braces, use doubled braces in the format template.

```echo
say("Hello, {}!".format("Echo"));           // Hello, Echo!
say("{0} + {1} = {2}".format(1, 2, 3));    // 1 + 2 = 3
say("Hello, {name}!".format({ name: "Echo" }));  // Hello, Echo!
say("{0} scored {points}".format("Ada", { points: 42 }));
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
Sorts the list **in place** in ascending order by default. Optionally accepts a comparator function that takes two arguments and returns a negative `int` (first before second), `0` (equal), or positive `int` (first after second). Pass a function value, a lambda, or a function name string.

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

### `map(f)`
Applies function value `f` to each element and returns a **new** list of results. `f` must take one argument. Does not mutate the input. Empty list returns `[]`. A callback that aborts aborts the call.

```echo
fn double(x: int) -> int {
    return x * 2;
}

nums: list = [1, 2, 3];
say(nums.map(double));    // [2, 4, 6]
say(map(nums, fn(x: int) -> int { return x + 1; }));    // [2, 3, 4]
```

Standalone keyword form:

```echo
say(map(items: nums, f: double));
```

---

### `filter(f)`
Returns a **new** list of elements, or a **new** hash of entries, for which `f` returns `true`. `f` must take one argument and return `bool` — `1` is a type error, not a kept element. On a hash, `f` receives each **value** (keys stay the same). Dispatches on the receiver / first argument: `list` or `hash`. Does not mutate the input. Empty list returns `[]`; empty hash returns `{}`. A callback that aborts aborts the call. Hash results preserve insertion order.

```echo
fn even(x: int) -> bool {
    return x % 2 == 0;
}

nums: list = [1, 2, 3, 4];
say(nums.filter(even));    // [2, 4]
say(filter(nums, fn(x: int) -> bool { return x > 2; }));    // [3, 4]

scores: hash = { a: 1, b: 2 };
say(scores.filter(even));    // {"b": 2}
say(filter(scores, even));
```

Standalone keyword form:

```echo
say(filter(items: nums, f: even));
say(filter(items: scores, f: even));
```

---

### `reduce(init, f)`
Folds binary function value `f` over the list, starting from required `init`, and returns the accumulated value. `f` must take exactly two arguments `(accumulator, element)`. Does not mutate the input. Empty list returns `init` and does not call `f`. A callback that aborts aborts the call. Each callback result must match `init`'s type.

```echo
fn add(acc: int, x: int) -> int {
    return acc + x;
}

nums: list = [1, 2, 3];
say(nums.reduce(0, add));    // 6
say(reduce(["a", "b"], "", fn(acc: str, item: str) -> str { return acc + item; }));    // ab
```

Standalone keyword form:

```echo
say(reduce(items: nums, init: 0, f: add));
```

---

### `forEach(f)`
Calls unary function value `f` on each element and discards the return value. Returns `null`. Does not mutate the input. Empty list does not call `f` and returns `null`. A callback that aborts aborts the call.

```echo
seen: list = [];
fn collect(x: int) {
    use mut seen;
    seen.push(x);
}

nums: list = [1, 2, 3];
say(nums.forEach(collect));    // null
say(seen);                     // [1, 2, 3]
say(forEach(nums, fn(x: int) { say(x); }));    // prints 1 2 3, then null
```

Standalone keyword form:

```echo
say(forEach(items: nums, f: collect));
```

---

### `flatMap(f)`
Applies unary function value `f` to each element. `f` must return a `list`. Concatenates those lists **one** level into a **new** list. Nested lists inside a callback result stay nested. Does not mutate the input. Empty list returns `[]`. A callback that aborts aborts the call.

```echo
fn wrap(x: int) -> list {
    return [x, x];
}

nums: list = [1, 2];
say(nums.flatMap(wrap));    // [1, 1, 2, 2]
say(flatMap([[1, 2], [3], []], fn(xs: list) -> list { return xs; }));    // [1, 2, 3]
```

Standalone keyword form:

```echo
say(flatMap(items: nums, f: wrap));
```

---

### `some(f)`
Returns `true` if unary `f` returns `true` for any element. `f` must take one argument and return `bool` — `1` is a type error. Empty list is `false`. Stops on the first `true`. Does not mutate the input. A callback that aborts aborts the call.

```echo
fn even(x: int) -> bool {
    return x % 2 == 0;
}

nums: list = [1, 2, 3];
say(nums.some(even));    // true
say(some(nums, fn(x: int) -> bool { return x > 10; }));    // false
```

Standalone keyword form:

```echo
say(some(items: nums, f: even));
```

---

### `every(f)`
Returns `true` if unary `f` returns `true` for every element. `f` must take one argument and return `bool` — `1` is a type error. Empty list is `true`. Stops on the first `false`. Does not mutate the input. A callback that aborts aborts the call.

```echo
fn positive(x: int) -> bool {
    return x > 0;
}

nums: list = [1, 2, 3];
say(nums.every(positive));    // true
say(every(nums, fn(x: int) -> bool { return x % 2 == 0; }));    // false
```

Standalone keyword form:

```echo
say(every(items: nums, f: positive));
```

---

### `findIndex(f)`
Returns the first index where unary `f` returns `true`, or `-1` if none match. `f` must take one argument and return `bool` — `1` is a type error. Empty list is `-1`. Stops on the first `true`. Does not mutate the input. A callback that aborts aborts the call. Distinct from `find(value)`, which still searches by value.

```echo
fn even(x: int) -> bool {
    return x % 2 == 0;
}

nums: list = [1, 2, 3];
say(nums.findIndex(even));    // 1
say(findIndex(nums, fn(x: int) -> bool { return x == 9; }));    // -1
say(nums.find(2));    // 1
```

Standalone keyword form:

```echo
say(findIndex(items: nums, f: even));
```

---

### `zip(right)`
Pairs this list with `right` into a **new** list of 2-element lists `[left[i], right[i]]`. Length is `min(len(left), len(right))` — unequal lengths are not an error. Empty either side returns `[]`. Does not mutate the inputs. List only. No N-way zip and no zipper callback.

```echo
left: list = [1, 2, 3];
right: list = [10, 20];
say(left.zip(right));    // [[1, 10], [2, 20]]
say(zip([1], []));       // []
```

Standalone keyword form:

```echo
say(zip(left: left, right: right));
```

---

### `unique()`
Returns a **new** list of first occurrences in original order, using Echo `==` (`true` is not `1`). Empty list returns `[]`. Does not mutate the input. List only.

```echo
nums: list = [1, 2, 1, 3, 2];
say(nums.unique());    // [1, 2, 3]
say(unique([true, 1, true, 1]));    // [true, 1]
```

Standalone keyword form:

```echo
say(unique(items: nums));
```

---

### `chunk(size)`
Splits this list into a **new** list of lists of length `size`. The last chunk may be shorter. `size` must be an `int` `>= 1`. Empty list returns `[]`. Does not mutate the input. List only.

```echo
nums: list = [1, 2, 3, 4, 5];
say(nums.chunk(2));    // [[1, 2], [3, 4], [5]]
say(chunk([], 3));     // []
```

Standalone keyword form:

```echo
say(chunk(items: nums, size: 2));
```

---

### `flatten()`
Concatenates **one** level of nested lists into a **new** list. Empty list returns `[]`. A top-level element that is not a list is a type error (**E2846**). Does not mutate the input. List only.

```echo
nums: list = [[1, 2], [3], []];
say(nums.flatten());    // [1, 2, 3]
say(flatten([[[1]], [2]]));    // [[1], 2]
```

Standalone keyword form:

```echo
say(flatten(items: nums));
```

---

### `partition(f)`
Returns a **new** two-element list `[matches, rest]`. Unary `f` must return `bool` (`true` keeps the element in `matches`; `1` is not kept). Empty list returns `[[], []]`. A callback that aborts aborts the whole call. Does not mutate the input. List only.

```echo
nums: list = [1, 2, 3, 4];
say(nums.partition(fn(x: int) -> bool { return x % 2 == 0; }));    // [[2, 4], [1, 3]]
```

Standalone keyword form:

```echo
say(partition(items: nums, f: even));
```

---

### `rangeList(start, end)`
Returns a **new** `list` of `int` with the same values as `for i in start...end` (exclusive end, step `1`). Empty when that loop would not iterate (`rangeList(0, 0)` is `[]`). Same value as the range expression `start...end`. Method form is not required.

```echo
say(rangeList(0, 5));    // [0, 1, 2, 3, 4]
say(rangeList(5, 3));    // []
```

Standalone keyword form:

```echo
say(rangeList(start: 0, end: 5));
```

---

### `rangeListInclusive(start, end)`
Same as `rangeList`, but matches `for i in start..end` (inclusive end). `rangeListInclusive(0, 0)` is `[0]`. Empty when `start > end` with step `1`.

```echo
say(rangeListInclusive(0, 5));    // [0, 1, 2, 3, 4, 5]
say(rangeListInclusive(0, 0));    // [0]
```

Standalone keyword form:

```echo
say(rangeListInclusive(start: 0, end: 5));
```

---

### `clone()`
Returns a **deep** copy of the list. Nested lists and hashes are copied recursively; the clone does not share nested structure with the original.

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

### `mapValues(f)`
Returns a **new** hash with the same keys. Unary `f` is called with each value. Empty hash returns `{}`. Does not mutate the input. A callback that aborts aborts the call. Preserves insertion order. Hash only.

```echo
fn double(x: int) -> int {
    return x * 2;
}

scores: hash = { a: 1, b: 2 };
say(scores.mapValues(double));    // {"a": 2, "b": 4}
say(mapValues(scores, fn(x: int) -> int { return x + 1; }));
```

Standalone keyword form:

```echo
say(mapValues(items: scores, f: double));
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
If `key` is missing, sets it to `default` and returns `default`. If present, returns the current value unchanged.

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
Returns a **deep** copy of the hash (nested lists/hashes copied recursively).

```echo
original: hash = { name: "Ada" };
copy: hash = original.clone();
copy["name"] = "Echo";
say(original["name"]);    // Ada
say(copy["name"]);        // Echo
```

Class instances also support `.clone()` (new instance, deep-copied fields).

---

## Notes

- Kwargs: all builtins except the variadics `say`, `eprint`, `format`, `pathJoin` (and note `pathJoin` is also variadic).
- Standalone collection calls use `items:` for the collection (`find`, `countOf`, `map`, `filter`, `reduce`, `forEach`, `flatMap`, `flatten`, `some`, `every`, `findIndex`, `unique`, `chunk`, `partition`, `mapValues`). `zip` uses `left:` / `right:`. `rangeList` / `rangeListInclusive` use `start:` / `end:`. `chunk` also uses `size:`. `partition` also uses `f:`.
- Conversions (`asInt`, `asIntOr`, `asFloat`, `asFloatOr`, `asBool`, `asString`, `type`) work standalone and as methods.
- Mutating list/hash methods interact with `watch` and `use mut`.
- `clone()` is deep for lists, hashes, and class instances (0.9.3).
- Named `format()` placeholders use a trailing hash (0.9.4).

## Common Mistakes

- Keyword args on variadic builtins (`say`, `eprint`, `format`, `pathJoin`)
- Non-string keys for hash index / hash methods
- `pull()` on an empty list
- More than one comparator to `order()`
- Expecting `filter` / `partition` / `some` / `every` / `findIndex` to keep truthy `1` (need `bool`)
- `reduce` without `init`, or a non-binary callback
- `forEach` with a non-unary callback, or expecting a list return
- `flatMap` callback that does not return a list, or expecting multi-level flatten
- `flatten` with a non-list top-level element, or expecting multi-level flatten
- Treating `findIndex(f)` as `find(value)`
- Treating unequal `zip` lengths as an error, or `unique` equating `true` and `1`
- `chunk` with `size` `0`, `bool`, or float
- Treating `rangeList(0, 5)` as inclusive (use `rangeListInclusive` or `0..5`)
- Expecting hash `filter` / `mapValues` to mutate

## See Also
- [Lists](/core-concepts/lists)
- [Hashes](/core-concepts/hashes)
- [Operators](/reference/operators)
- [Language Reference](/reference/language-reference)
